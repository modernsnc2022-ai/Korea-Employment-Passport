/* Nepal E-9 stage navigator. Informational preview ONLY; fail closed. */
(() => {
  'use strict';

  const ROUTE_ID = 'np-e9-manufacturing-2026';
  const DATA_PATHS = [
    'data/np_e9_manufacturing_2026.json',
    'data/np_e9_manufacturing_2026_ne.json',
    'data/np_stage_readiness_2026.json',
    'data/np_document_packs_2026.json',
    'data/np_notice_provenance_2026.json',
    'data/np_eps_topik_preparation_2026.json'
  ];

  // URL-to-purpose binding: an unexpected, forged or wrong-cohort source
  // fails closed rather than silently replacing a study link.
  const PREP_SOURCES = Object.freeze({
    hrd_standard_textbooks: 'https://epstopik.hrdkorea.or.kr/epstopik/book/std/standardBookList.do?lang=en',
    hrd_public_questions: 'https://epstopik.hrdkorea.or.kr/epstopik/book/pub/publicWorkBookList.do?lang=ko',
    hrd_exam_schedule: 'https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/sechduleDetail.do?examNation=006&examNot=90&examYear=2026&lang=ko&lcnsId=001',
    nepal_official_notices: 'https://epsnepal.gov.np/notices'
  });
  const PREP_AUDIENCES = Object.freeze({
    hrd_standard_textbooks: ['current', 'future'],
    hrd_public_questions: ['current', 'future'],
    hrd_exam_schedule: ['current'],
    nepal_official_notices: ['current', 'future']
  });
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
    // Never publish baseline fees or exhaustive checklists as instructions for
    // a cohort whose exact current rules have not been authenticated.
    const unverified = classification.code === 'hold' || classification.code === 'reference';
    const actionText = unverified
      ? 'यो चरणको प्रक्रिया रहेको पुष्टि भए पनि, हालको २०२६ पहिलो चरणका लागि ठ्याक्कै शुल्क, ' +
        'आवश्यक कागजात, परीक्षण केन्द्र, समयसीमा तथा पेश गर्ने स्थान KEP ले पुष्टि गरेको छैन। ' +
        'आफ्नो समूहको नयाँ आधिकारिक सूचना प्राप्त नभएसम्म कुनै शुल्क नतिर्नुहोस् र पुरानो सूचीका आधारमा कागजात नबुझाउनुहोस्।'
      : (localized?.action || stage.action);
    target.append(element('p', actionText, 'action-text'));

    if (stage.warning && !unverified) target.append(element('p', 'सावधानी: ' + stage.warning, 'warning'));
    if (classification.group?.note) {
      // Upstream evidence notes are authored in English, while the interface
      // is Nepali. Set the actual source language for screen readers.
      const note = element('p', classification.group.note, 'provenance');
      note.lang = 'en';
      target.append(note);
    }

    const original = classification.group?.currentSource || stage.sourceUrl;
    addOfficialLink(target, original, classification.code === 'reference'
      ? 'आधिकारिक प्रक्रियाको स्रोत खोल्नुहोस् ↗'
      : 'यो चरणसम्बन्धी आधिकारिक सूचना हेर्नुहोस् ↗');
    if (classification.code === 'closed' && ['registration','document_verify'].includes(stage.id)) {
      addOfficialLink(target, readiness.currentCohort?.recruitmentRegistration?.crossSourceSchedule?.extensionNoticeUrl,
        '२०२६ को आवेदन म्याद थप तथा राहदानीको आधिकारिक पूरक सूचना ↗');
    }
    if (classification.code === 'closed' && ['registration','exam_fee','document_verify'].includes(stage.id)) {
      addOfficialLink(target, 'https://epsnepal.gov.np/postdetails/137', '२०२६ को आवेदन/भुक्तानी सुरक्षा सूचना ↗');
    }
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
        if (pack.warning && !unverified) section.append(element('p', pack.warning, 'warning'));
        if (!unverified && isCurrent) {
          const ul = element('ul');
          for (const item of pack.items || []) ul.append(element('li', item.label + ' — ' + item.rule));
          section.append(ul);
          addOfficialLink(section, pack.sourceUrl, 'यो कागजात सूचीको आधिकारिक स्रोत ↗');
        } else {
          section.append(element('p',
            'हालको २०२६ पहिलो चरणका लागि कागजात वा शुल्कको विस्तृत सूची आधिकारिक रूपमा प्रमाणीकरण नभएकाले यहाँ देखाइएको छैन।',
            'warning'));
        }
      }
      target.append(section);
    }
    target.append(element('p', 'यहाँबाट कुनै सरकारी आवेदन पठाइँदैन। वास्तविक आवेदन आधिकारिक पोर्टलमा मात्र गर्नुपर्छ।', 'provenance'));
  }
  const NOTICE_TAGS = Object.freeze({
    verified_current_primary: '२०२६ पहिलो चरणको मुख्य सूचना',
    verified_current_supplement: '२०२६ पहिलो चरणको प्रमाणित पूरक सूचना',
    supplementary_unreviewed: 'थप सूचना — पूरा सामग्री समीक्षा बाँकी',
    prior_2025_cohort: '२०२५ समूहको सूचना — २०२६ मा लागू हुँदैन',
    cohort_not_linked: 'प्रस्थान सूचना — हालको आवेदन समूहसँग सम्बन्ध अपुष्ट',
    other_2026_program: '२०२६ को अर्को कार्यक्रम — Manufacturing पहिलो चरणमा लागू हुँदैन'
  });
  function assertSafeNoticeLedger(ledger, readiness) {
    if (ledger?.routeId !== ROUTE_ID || ledger.policy?.betaAccess !== 'blocked' ||
        ledger.policy?.allowDeadlineExtensionInference !== false ||
        ledger.policy?.allowDepartureToPromote2026ApplicationStages !== false ||
        ledger.policy?.allowCrossSectorPromotion !== false ||
        !Array.isArray(ledger.notices) || !ledger.notices.length) {
      throw new Error('Nepal notice provenance safety gate mismatch');
    }
    const ext = readiness?.currentCohort?.recruitmentRegistration?.crossSourceSchedule;
    if (ext?.deadlineExtensionVerified !== true ||
        ext?.finalVerifiedRegistrationPeriod !== '2026-07-27 through 2026-08-05' ||
        ext?.extensionNoticeUrl !== 'https://epsnepal.gov.np/postdetails/143' ||
        readiness?.currentCohort?.recruitmentRegistration?.status !== 'closed_verified') {
      throw new Error('Unverified Nepal deadline promotion');
    }
    const ids = new Set();
    for (const notice of ledger.notices) {
      if (ids.has(notice.id) || !NOTICE_TAGS[notice.applicability] ||
          !safeOfficialLink(notice.url) || !/^2026-[0-9]{2}-[0-9]{2}$/.test(notice.date) ||
          !notice.title || !notice.ruleImpact) throw new Error('Invalid Nepal notice provenance');
      if (notice.applicability === 'verified_current_primary' &&
          (notice.cohort !== '2026_first_phase_manufacturing' ||
           notice.reviewState !== 'full_primary_document_reviewed')) {
        throw new Error('Unverified current-cohort promotion');
      }
      if (notice.applicability === 'verified_current_supplement') {
        const matches = notice.cohort === '2026_first_phase_manufacturing' && (
          (notice.id === 'np_2026_passport_0730' && notice.url === 'https://epsnepal.gov.np/postdetails/143' && notice.reviewState === 'official_inline_image_reviewed') ||
          (notice.id === 'np_2026_urgent_0726' && notice.url === 'https://epsnepal.gov.np/postdetails/137' && notice.reviewState === 'scanned_notice_pages_1_to_3_reviewed_appendix_guide_not_promoted')
        );
        if (!matches) throw new Error('Unverified supplemental cohort change');
      }
      if (notice.applicability === 'prior_2025_cohort' && notice.cohort !== '2025_manufacturing') {
        throw new Error('Prior cohort label invalid');
      }
      if (notice.applicability === 'other_2026_program' &&
          notice.cohort !== '2026_root_industry_distinct_program') {
        throw new Error('Other-program label invalid');
      }
      if (notice.applicability === 'cohort_not_linked' &&
          !notice.cohort.startsWith('departure_')) {
        throw new Error('Departure cohort label invalid');
      }
      ids.add(notice.id);
    }
    const passport = ledger.notices.find(n => n.id === 'np_2026_passport_0730');
    const urgent = ledger.notices.find(n => n.id === 'np_2026_urgent_0726');
    if (passport?.applicability !== 'verified_current_supplement' ||
        urgent?.applicability !== 'verified_current_supplement') throw new Error('Required supplements not authenticated');
  }
  function renderNoticeLedger(ledger) {
    const target = $('noticeReview');
    target.replaceChildren();
    target.append(element('h2', 'हालसम्म जाँचिएका आधिकारिक सूचनाहरू'));
    target.append(element('p',
      'सूचनाको मिति नयाँ हुनु मात्रले त्यो २०२६ पहिलो चरणका नयाँ परीक्षार्थीलाई लागू हुन्छ भन्ने हुँदैन। ' +
      'यहाँको समीक्षा ' + ledger.reviewedAt + ' मा गरिएको थियो; पछिल्लो सूचना सरकारी साइटबाट जाँच्नुहोस्।',
      'caution'));
    for (const notice of ledger.notices) {
      const item = element('article', undefined, 'notice-item');
      item.append(element('p', NOTICE_TAGS[notice.applicability], 'state state-reference'));
      const heading = element('h3', notice.date + ' · ' + notice.title);
      heading.lang = 'en';
      item.append(heading);
      const evidence = element('p', notice.ruleImpact, 'provenance');
      evidence.lang = 'en';
      item.append(evidence);
      addOfficialLink(item, notice.url, 'यो आधिकारिक सूचना खोल्नुहोस् ↗');
      target.append(item);
    }
    addOfficialLink(target, 'https://epsnepal.gov.np/notices', 'सरकारी सूचना सूचीमा नयाँ सूचना जाँच्नुहोस् ↗');
  }
  function assertSafePreparation(prep, readiness) {
    if (prep?.routeId !== ROUTE_ID || prep.country !== 'NP' ||
        prep.scope !== 'general_eps_topik_korean_learning_only' ||
        prep.status !== 'reference_only' || prep.betaStatus !== 'blocked' ||
        prep.applicationStatus !== 'closed_2026_first_phase' ||
        prep.examinationDates !== 'undecided' ||
        JSON.stringify(prep.cohortVisibility) !== JSON.stringify(['current', 'future']) ||
        prep.privacy?.requiresSignIn !== false || prep.privacy?.collectsPersonalData !== false ||
        prep.privacy?.tracksOfficialMilestones !== false ||
        prep.privacy?.persistsStudyProgress !== false ||
        readiness?.currentCohort?.epsTopikSchedule?.status !==
          'verified_hrd_current_row_test_dates_undecided' ||
        !prep.studySequenceAdviceNe || !Array.isArray(prep.resources) || prep.resources.length !== 4) {
      throw new Error('Nepal study resources must remain reference-only and beta-blocked');
    }
    const seen = new Set();
    for (const item of prep.resources) {
      if (!Object.prototype.hasOwnProperty.call(PREP_SOURCES, item.id) ||
          seen.has(item.id) || PREP_SOURCES[item.id] !== item.sourceUrl ||
          !safeOfficialLink(item.sourceUrl) ||
          item.sourceStatus?.startsWith('verified_') !== true ||
          JSON.stringify(item.cohortVisibility) !== JSON.stringify(PREP_AUDIENCES[item.id]) ||
          !item.titleNe || !item.descriptionNe) {
        throw new Error('Invalid Nepal official study material provenance');
      }
      seen.add(item.id);
    }
  }
  function renderPreparation(prep, choice) {
    const target = $('prepResources');
    target.hidden = choice === 'other';
    const list = $('prepResourceList');
    list.replaceChildren();
    if (choice === 'other') return;
    list.append(element('p', prep.descriptionNe, 'caution'));
    list.append(element('p', prep.studySequenceAdviceNe, 'np-prep-advice'));
    for (const entry of prep.resources) {
      if (!entry.cohortVisibility.includes(choice)) continue;
      const section = element('article', undefined, 'np-prep-resource');
      section.append(element('h3', entry.titleNe));
      section.append(element('p', entry.descriptionNe));
      addOfficialLink(section, entry.sourceUrl, entry.titleNe + ' — आधिकारिक स्रोत ↗');
      list.append(section);
    }
    list.append(element('p',
      'प्रश्न अभ्यास सामग्री वास्तविक २०२६ परीक्षाको प्रश्नपत्र होइन। ' +
      'कुनै व्यक्तिगत कागजात, फोन नम्बर वा भुक्तानी यहाँ नदिनुहोस्।',
      'np-prep-disclaimer'));
  }
  function renderApplicantCohort(choice, readiness) {
    const current = choice === 'current';
    $('stagePicker').hidden = !current;
    $('stageDetail').hidden = !current;
    const guide = $('cohortGuidance');
    guide.hidden = current;
    guide.replaceChildren();
    if (current) return;
    if (choice === 'future') {
      guide.append(element('h2', 'अर्को Manufacturing आवेदनको आधिकारिक सूचना पर्खनुहोस्'));
      guide.append(element('p',
        '२०२६ प्रथम चरणको आवेदन बन्द छ। भविष्यको कुनै नयाँ आवेदन मिति, शुल्क, योग्यता वा कागजात ' +
        'अहिले KEP ले पुष्टि गरेको छैन। पुरानो आवेदन फाराम/सामग्री प्रयोग नगर्नुहोस्।'));
      guide.append(element('p', 'आधिकारिक EPS नेपाल पृष्ठमा नयाँ आवेदन घोषणा आएपछि मात्र नयाँ समूहको निर्देशन लागू गर्न सकिन्छ।', 'caution'));
    } else {
      guide.append(element('h2', 'तपाईंको अलग EPS आवेदन समूहका लागि यो २०२६ पहिलो चरणको मार्गदर्शन लागू हुँदैन'));
      guide.append(element('p',
        '२०२५ का आवेदक, पुनःभर्ना/Root Industry का उम्मेदवार वा अन्य क्षेत्रको प्रक्रियाका लागि ' +
        'आफ्नो परीक्षा र आवेदन समूह उल्लेख गरिएको सरकारी सूचना मात्र पालना गर्नुहोस्।'));
      guide.append(element('p', '२०२६ पहिलो चरण Manufacturing का मिति वा कागजात तपाईंको समूहका लागि स्वतः लागू हुँदैनन्।', 'caution'));
    }
    addOfficialLink(guide, readiness.officialNoticeIndex, 'EPS नेपालका आधिकारिक सूचना हेर्नुहोस् ↗');
    guide.append(element('p', 'KEP ले यहाँ नयाँ आवेदन, beta access वा विद्यार्थीको व्यक्तिगत विवरण सङ्कलन गर्दैन।', 'provenance'));
  }
  async function start() {
    const [pack, translations, readiness, documents, ledger, preparation] = await Promise.all(DATA_PATHS.map(json));
    if (pack.country !== 'NP' || pack.cycle !== 2026 || pack.lifecycle !== 'research_hold' ||
        pack.safety?.betaIntakeOpen !== false || readiness.routeId !== ROUTE_ID ||
        readiness.betaReadiness?.status !== 'blocked' || documents.routeId !== ROUTE_ID ||
        !Array.isArray(pack.stages)) throw new Error('Nepal beta safety gate mismatch');
    assertSafeNoticeLedger(ledger, readiness);
    assertSafePreparation(preparation, readiness);

    $('verifiedAt').textContent = readiness.checkedAt || 'अज्ञात';
    $('statusSummary').textContent =
      'यो अनुसन्धान पूर्वावलोकन हो। २०२६ पहिलो चरणको आवेदन म्याद ५ अगस्टसम्म थपिएको थियो र अहिले बन्द छ। ' +
      'हालको EPS-TOPIK परीक्षा मिति, Skill Test तथा पछिल्ला रोजगारी चरणका सबै नियम ' +
      'अझै पुष्टि भएका छैनन्। वास्तविक beta access उपलब्ध छैन।';
    addOfficialLink($('summaryLinks'), readiness.officialNoticeIndex, 'सरकारी EPS सूचनाहरू ↗');

    const stages = pack.stages.filter(s => !String(s.supportState).startsWith('no_separate_step_verified'));
    const select = $('stageSelect');
    select.replaceChildren();
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

    // This Set is intentionally ONLY in this page's JS heap:
    // no localStorage, cookies, server calls, URLs or applicant identity.
    // It records reading of KEP guidance, NEVER official EPS completion.
    const readStages = new Set();
    const stageLabel = stage => translations[stage.id]?.title || stage.title;
    const updateTracker = () => {
      const currentId = select.value;
      const marked = readStages.has(currentId);
      const progress = $('reviewProgress');
      progress.max = stages.length;
      progress.value = readStages.size;
      $('reviewStatus').textContent =
        'यो सत्रमा ' + readStages.size + ' / ' + stages.length +
        ' चरणको विवरण पढेको चिन्ह लगाइएको छ। सरकारी प्रक्रिया पूरा भएको गणना होइन।';
      const button = $('stageReviewBtn');
      button.textContent = marked ? 'यो चरणको पढेको चिन्ह हटाउनुहोस्' : 'यो चरणको जानकारी पढेँ';
      button.setAttribute('aria-pressed', String(marked));
      $('resetStageReviewBtn').hidden = readStages.size === 0;
      const details = $('reviewedDetails');
      details.hidden = readStages.size === 0;
      if (!readStages.size) details.open = false;
      const list = $('reviewedStageList');
      list.replaceChildren();
      for (const stage of stages) {
        if (readStages.has(stage.id)) list.append(element('li', stageLabel(stage)));
      }
    };
    const update = () => {
      const position = stages.findIndex(s => s.id === select.value);
      const stage = stages[position];
      if (stage) renderDetail(stage, translations[stage.id], readiness, documents);
      $('stagePosition').textContent =
        'हेर्दै गरेको चरण ' + (position + 1) + ' / ' + stages.length +
        ' — सरकारी प्रक्रिया पूरा भएको सङ्केत होइन।';
      $('prevStageBtn').disabled = position <= 0;
      $('nextStageBtn').disabled = position === -1 || position >= stages.length - 1;
      updateTracker();
    };
    // Navigation changes only the locally displayed guidance, never actual EPS
    // progress, eligibility, government registration or applicant records.
    const stepBy = delta => {
      if ($('cohortSelect').value !== 'current') return;
      const index = stages.findIndex(s => s.id === select.value);
      const destination = index + delta;
      if (index < 0 || destination < 0 || destination >= stages.length) return;
      select.value = stages[destination].id;
      update();
    };
    $('prevStageBtn').addEventListener('click', () => stepBy(-1));
    $('nextStageBtn').addEventListener('click', () => stepBy(1));
    select.addEventListener('change', update);
    $('stageReviewBtn').addEventListener('click', () => {
      if ($('cohortSelect').value !== 'current' || !stages.some(s => s.id === select.value)) return;
      if (readStages.has(select.value)) readStages.delete(select.value);
      else readStages.add(select.value);
      updateTracker();
    });
    $('resetStageReviewBtn').addEventListener('click', () => {
      readStages.clear();
      updateTracker();
    });
    const cohortSelect = $('cohortSelect');
    const refreshCohort = () => {
      const current = cohortSelect.value === 'current';
      if (!current && readStages.size) readStages.clear();
      renderApplicantCohort(cohortSelect.value, readiness);
      renderPreparation(preparation, cohortSelect.value);
      $('reviewTracker').hidden = !current;
      updateTracker();
    };
    cohortSelect.addEventListener('change', refreshCohort);
    update();
    refreshCohort();
    renderNoticeLedger(ledger);
    $('previewBody').hidden = false;
  }

  start().catch(() => {
    $('statusSummary').textContent =
      'नेपाली आधिकारिक स्रोत/सुरक्षा स्थिति अहिले लोड हुन सकेन। पुरानो जानकारी प्रयोग नगर्नुहोस्।';
    $('loadError').hidden = false;
    $('previewBody').hidden = true;
  });
})();
