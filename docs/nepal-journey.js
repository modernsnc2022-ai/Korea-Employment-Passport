/* Nepal E-9 stage navigator. Informational preview ONLY; fail closed. */
(() => {
  'use strict';

  const ROUTE_ID = 'np-e9-manufacturing-2026';
  const DATA_PATHS = [
    'data/np_e9_manufacturing_2026.json',
    'data/np_e9_manufacturing_2026_ne.json',
    'data/np_stage_readiness_2026.json',
    'data/np_document_packs_2026.json'
  ];
  const LABELS = Object.freeze({
    closed: { title: '२०२६ आवेदन अवधि बन्द', detail: 'यो पहिलो चरणको पुरानो आवेदन अवधि हो। नयाँ आवेदन खुलेको मान्न मिल्दैन।' },
    waiting: { title: 'नयाँ आधिकारिक सूचना पर्खनुहोस्', detail: 'हालको २०२६ समूहका लागि मिति वा नतिजा KEP मा पुष्टि गरिएको छैन। अनुमान नगर्नुहोस्।' },
    hold: { title: 'यो चरण अझै प्रमाणीकरणमा छ', detail: 'हालको समूहको आधिकारिक सूचना बिना शुल्क, अस्पताल, कागजात वा मिति निश्चित नमान्नुहोस्।' },
    reference: { title: 'प्रक्रियाको जानकारी मात्र', detail: 'यो सामान्य प्रक्रिया हो; हालको २०२६ समूहमा लागू हुने मिति वा ठ्याक्कै नियमको पुष्टि होइन।' }
  });

  const $ = id => document.getElementById(id);
  function element(tag, text, className) {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = String(text);
    if (className) e.className = className;
    return e;
  }
  function safeOfficialLink(value) {
    try {
      const u = new URL(value);
      const host = u.hostname.toLowerCase();
      return u.protocol === 'https:' && (
        host === 'epsnepal.gov.np' || host === 'epstopik.hrdkorea.or.kr' ||
        host === 'eps.hrdkorea.or.kr' || host === 'www.hikorea.go.kr' ||
        host === 'www.visa.go.kr' || host === 'feims.dofe.gov.np' ||
        host === 'www.minimumwage.go.kr'
      ) ? u.href : '';
    } catch { return ''; }
  }
  function categoryFor(stageId, readiness) {
    const c = readiness.currentCohort || {};
    const matches = key => Array.isArray(c[key]?.stageIds) && c[key].stageIds.includes(stageId);
    if (matches('recruitmentRegistration')) return { code: 'closed', group: c.recruitmentRegistration };
    if (matches('epsTopikSchedule')) return { code: 'waiting', group: c.epsTopikSchedule };
    if (matches('epsTopikResult')) return { code: 'waiting', group: c.epsTopikResult };
    if (matches('skillCompetency')) return { code: 'waiting', group: c.skillCompetency };
    if (matches('medicalAndJobApplication')) return { code: 'hold', group: c.medicalAndJobApplication };
    if (matches('postSelectionVisaDeparture')) return { code: 'hold', group: c.postSelectionVisaDeparture };
    return { code: 'reference', group: null };
  }
  function addOfficialLink(parent, url, caption) {
    const href = safeOfficialLink(url);
    if (!href) return;
    const a = element('a', caption, 'official-link');
    a.href = href;
    a.rel = 'noopener noreferrer';
    a.target = '_blank';
    parent.append(a);
  }
  async function json(path) {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to load ' + path);
    return response.json();
  }
  function renderDetail(stage, localized, readiness, documentPacks) {
    const target = $('stageDetail');
    target.replaceChildren();
    const classification = categoryFor(stage.id, readiness);
    const label = LABELS[classification.code];
    target.append(element('p', label.title, 'state state-' + classification.code));
    target.append(element('h2', localized?.title || stage.title));
    target.append(element('p', label.detail, 'caution'));
    const lead = element('p', localized?.action || stage.action, 'action-text');
    target.append(lead);

    if (stage.warning) target.append(element('p', 'सावधानी: ' + stage.warning, 'warning'));
    if (classification.group?.note) target.append(element('p', classification.group.note, 'provenance'));

    const original = classification.group?.currentSource || stage.sourceUrl;
    addOfficialLink(target, original, classification.code === 'reference'
      ? 'आधिकारिक प्रक्रियाको स्रोत खोल्नुहोस् ↗'
      : 'यो चरणसम्बन्धी आधिकारिक सूचना हेर्नुहोस् ↗');
    if (classification.code !== 'closed') {
      addOfficialLink(target, readiness.officialNoticeIndex, 'नेपाल EPS को पछिल्लो सूचना हेर्नुहोस् ↗');
    }

    const packs = (documentPacks.packs || []).filter(p => p.appliesTo?.includes(stage.id));
    if (packs.length) {
      const section = element('section', undefined, 'document-pack');
      section.append(element('h3', 'कागजातसम्बन्धी जानकारी'));
      for (const pack of packs) {
        section.append(element('h4', pack.title));
        const isCurrent = pack.status === 'verified_official_pdf';
        section.append(element('p', isCurrent
          ? 'मुख्य आधिकारिक सूचनाबाट पुष्टि भएको सूची; पछि आएका पूरक सूचनाले नियम परिवर्तन गरेको हुन सक्छ।'
          : 'पुरानो/सामान्य प्रक्रिया मात्र। हालको २०२६ आवेदनका लागि अन्तिम आवश्यक कागजातको सूची होइन।', 'caution'));
        if (pack.warning) section.append(element('p', pack.warning, 'warning'));
        const ul = element('ul');
        for (const item of pack.items || []) ul.append(element('li', item.label + ' — ' + item.rule));
        section.append(ul);
        addOfficialLink(section, pack.sourceUrl, 'यो कागजात सूचीको आधिकारिक स्रोत ↗');
      }
      target.append(section);
    }
    target.append(element('p', 'यहाँबाट कुनै सरकारी आवेदन पठाइँदैन। वास्तविक आवेदन आधिकारिक पोर्टलमा मात्र गर्नुपर्छ।', 'provenance'));
  }
  async function start() {
    const [pack, translations, readiness, documents] = await Promise.all(DATA_PATHS.map(json));
    if (pack.country !== 'NP' || pack.cycle !== 2026 || pack.lifecycle !== 'research_hold' ||
        pack.safety?.betaIntakeOpen !== false || readiness.routeId !== ROUTE_ID ||
        readiness.betaReadiness?.status !== 'blocked' || documents.routeId !== ROUTE_ID ||
        !Array.isArray(pack.stages)) throw new Error('Nepal beta safety gate mismatch');

    $('verifiedAt').textContent = readiness.checkedAt || 'अज्ञात';
    $('statusSummary').textContent =
      'यो अनुसन्धान पूर्वावलोकन हो। २०२६ को पहिलो चरणको आवेदन अवधि बन्द छ। ' +
      'हालको EPS-TOPIK परीक्षा मिति, Skill Test तथा पछिल्ला रोजगारी चरणका सबै नियम ' +
      'अझै पुष्टि भएका छैनन्। वास्तविक beta access उपलब्ध छैन।';
    addOfficialLink($('summaryLinks'), readiness.officialNoticeIndex, 'सरकारी EPS सूचनाहरू ↗');

    const stages = pack.stages.filter(s => !String(s.supportState).startsWith('no_separate_step_verified'));
    const select = $('stageSelect');
    for (const stage of stages) {
      const title = translations[stage.id]?.title || stage.title;
      const option = element('option', title);
      option.value = stage.id;
      select.append(option);
    }
    if (!stages.length) throw new Error('No Nepal stages');
    const requested = new URLSearchParams(window.location.search).get('stage');
    const selected = stages.some(s => s.id === requested) ? requested : 'registration';
    select.value = stages.some(s => s.id === selected) ? selected : stages[0].id;
    const update = () => {
      const stage = stages.find(s => s.id === select.value);
      if (stage) renderDetail(stage, translations[stage.id], readiness, documents);
    };
    select.addEventListener('change', update);
    update();
    $('previewBody').hidden = false;
  }

  start().catch(() => {
    $('statusSummary').textContent =
      'नेपाली आधिकारिक स्रोत/सुरक्षा स्थिति अहिले लोड हुन सकेन। पुरानो जानकारी प्रयोग नगर्नुहोस्।';
    $('loadError').hidden = false;
    $('previewBody').hidden = true;
  });
})();
