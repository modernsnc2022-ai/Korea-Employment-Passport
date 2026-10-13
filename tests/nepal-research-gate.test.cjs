'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const gateText = fs.readFileSync(path.join(root, 'scripts/check_nepal_research_gate.js'), 'utf8')
  .replace(/^#![^\n]*\n/, '');
const dataRoot = path.join(root, 'docs/data');

function executeGate(modify) {
  const cloned = new Map();
  const messages = [];
  const errors = [];
  const processStub = { exitCode: 0 };
  const fsStub = {
    readFileSync(filename) {
      const name = path.basename(filename);
      if (!cloned.has(name)) {
        cloned.set(name, JSON.parse(fs.readFileSync(path.join(dataRoot, name), 'utf8')));
      }
      const state = cloned.get(name);
      if (modify) modify(name, state);
      return JSON.stringify(state);
    }
  };
  const context = {
    require: (name) => {
      if (name === 'node:fs') return fsStub;
      if (name === 'node:path') return path;
      throw new Error('unexpected module: ' + name);
    },
    __dirname: path.join(root, 'scripts'),
    process: processStub,
    console: {
      log: (...args) => messages.push(args.join(' ')),
      error: (...args) => errors.push(args.join(' '))
    }
  };
  vm.runInNewContext(gateText, context, { filename: 'check_nepal_research_gate.js', timeout: 3000 });
  return { exitCode: processStub.exitCode, messages, errors };
}

test('Nepal current research data passes, but beta is still blocked', () => {
  const result = executeGate();
  assert.equal(result.exitCode, 0);
  assert.ok(result.messages.some(x => x.includes('NEPAL_RESEARCH_GATE_PASS')));
  assert.ok(result.messages.some(x => x.includes('beta=blocked')));
});

const safetyCases = [
  {
    name: 'blocks Nepal beta activation',
    mutate(file, data) {
      if (file === 'np_stage_readiness_2026.json') data.betaReadiness.status = 'open';
    }
  },
  {
    name: 'blocks Root Industry being promoted as manufacturing',
    mutate(file, data) {
      if (file === 'np_notice_provenance_2026.json')
        data.notices.find(x => x.id === 'np_2026_root_industry_alt_0701').applicability = 'verified_current_primary';
    }
  },
  {
    name: 'blocks unreviewed passport notice being promoted',
    mutate(file, data) {
      if (file === 'np_notice_provenance_2026.json')
        data.notices.find(x => x.id === 'np_2026_passport_0730').applicability = 'verified_current_primary';
    }
  },
  {
    name: 'blocks removal of verified official deadline extension',
    mutate(file, data) {
      if (file === 'np_stage_readiness_2026.json')
        data.currentCohort.recruitmentRegistration.crossSourceSchedule.deadlineExtensionVerified = false;
    }
  },
  {
    name: 'blocks Indonesia-only psychology stage in Nepal',
    mutate(file, data) {
      if (file === 'np_e9_manufacturing_2026.json')
        data.stages.find(x => x.id === 'psychology_pre_job').supportState = 'verified_current';
    }
  },
  {
    name: 'blocks unverified baseline without a warning',
    mutate(file, data) {
      if (file === 'np_document_packs_2026.json')
        data.packs.find(x => x.id === 'np_ccvi_visa_baseline').warning = '';
    }
  },
  {
    name: 'rejects a forged extension notice URL',
    mutate(file, data) {
      if (file === 'np_stage_readiness_2026.json')
        data.currentCohort.recruitmentRegistration.crossSourceSchedule.extensionNoticeUrl = 'https://epsnepal.gov.np/postdetails/136';
    }
  },
  {
    name: 'rejects an extension date unsupported by the reviewed image',
    mutate(file, data) {
      if (file === 'np_stage_readiness_2026.json')
        data.currentCohort.recruitmentRegistration.crossSourceSchedule.finalVerifiedRegistrationPeriod = '2026-07-27 through 2026-08-06';
    }
  },
  {
    name: 'rejects a reviewed supplement reassigned to Root Industry',
    mutate(file, data) {
      if (file === 'np_notice_provenance_2026.json')
        data.notices.find(x => x.id === 'np_2026_passport_0730').cohort = '2026_root_industry_distinct_program';
    }
  },
  {
    name: 'rejects old August 2 date as final registration deadline',
    mutate(file, data) {
      if (file === 'np_e9_manufacturing_2026.json')
        data.currentApplicationWindow.closesAt = '2026-08-02';
    }
  },
  {
    name: 'rejects stale exact-answer catalog after official extension',
    mutate(file, data) {
      if (file === 'np_exact_answer_rules_2026.json')
        data.answers.find(x => x.id === 'np_2026_application_window').sourceUrl = 'https://epsnepal.gov.np/postdetails/136';
    }
  }
];

for (const scenario of safetyCases) {
  test(scenario.name, () => {
    const result = executeGate(scenario.mutate);
    assert.equal(result.exitCode, 1);
    assert.ok(result.errors.some(x => x.startsWith('NEPAL_GATE_FAIL:')));
  });
}
