// Test v39 _reactKeyword function - inline implementation
const REPLY_POOL = {
  correct:   ['啱晒！你真聰明！', '冇錯啦，你好叻呀！', '答得啱，正呀！', 'Bingo！', '100分！'],
  wrong:     ['差少少啫，再諗下？', '唔緊要，再嚟一次！', '錯咗少少，加油！', '差一啲啲咋，唔好放棄！'],
  sad:       ['唔緊要㗎，我都陪住你。', '我哋一齊面對啦。', '你唔係一個人喎。'],
  happy:     ['叻仔！繼續加油！', '好嘢！', 'Yeah！', '你最棒啦！'],
  angry:     ['唔好嬲咁多啦，深呼吸。', '冷靜啲，你得嘅。'],
  shy:       ['你...你望住我嚟做咩...', '我會害羞㗎...'],
  surprised: ['嘩，咁都得？！', '哇！', '乜料咁都可以！'],
  neutral:   ['嗯嗯，我喺度聽緊。', '我聽緊你講。', '我喺度。'],
};
function _reactRandomPick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function _reactKeyword(text) {
  const t = (text || '').toLowerCase();
  if (!t.trim()) return { emotion: 'neutral', action: null, reply: _reactRandomPick(REPLY_POOL.neutral) };

  const HAPPY_KW = [
    '啱', '啱嘅', '答啱', 'correct', 'right', '✓', '✅', 'yes', 'yes!',
    '開心', '高興', '興奮', '快樂', '好嘢', '棒', '叻', '正', '爽', '甜',
    '笑', '哈哈', '嘻嘻', '開心死', '完美', '成功', 'yeah', 'yay', 'happy',
    'joy', 'great', 'good', 'wonderful', 'amazing', 'love', 'loved',
    '鍾意', '中意', '喜歡', '太正', '勁', '犀利', 'like', '做咗',
  ];
  const SAD_KW = [
    '錯', '唔啱', '答錯', 'wrong', '✗', '❌', 'no!', 'no', '失敗', '唔得',
    '慘', '傷心', '痛', '哭', '喊', '心痛', '心碎', '心淡', '灰', '灰心',
    '絕望', '失望', '累', '攰', '辛苦', '難過', '難受', '唔開心', '煩',
    'sad', 'cry', 'tired', 'hurt', 'bad', 'terrible', 'awful', 'depressed',
    'lonely', '寂寞', '孤獨', '無助', 'miserable', '失戀',
    '不舒服', '唔舒服', '唔爽', '辛苦', '攰', '病', '病咗',
  ];
  const ANGRY_KW = [
    '嬲', '嬲爆', '嬲死', '激嬲', '燥', '火大', '氣死', '激死', 'angry',
    'mad', 'furious', 'hate', 'hated', 'pissed', 'rage', '討厭',
  ];
  const SHY_KW = [
    '害羞', '怕羞', '紅臉', '臉紅', '紅晒', '不好意思', '唔好意思', 'shy',
    'embarrass', 'blush',
  ];
  const SURPRISED_KW = [
    '驚', '驚死', '怕', '嚇', '嘩', '哇', '竟然', '居然', '估唔到',
    '諗唔到', 'surprise', 'wow', 'omg', 'shock', 'amazing',
  ];

  function scoreOf(list) { let n = 0; for (const w of list) if (w && t.indexOf(w) !== -1) n++; return n; }
  const scores = {
    happy: scoreOf(HAPPY_KW),
    sad: scoreOf(SAD_KW),
    angry: scoreOf(ANGRY_KW),
    shy: scoreOf(SHY_KW),
    surprised: scoreOf(SURPRISED_KW),
  };

  if (/!{2,}/.test(t)) scores.happy += 0.5;
  if (/\?{2,}/.test(t)) scores.surprised += 0.5;
  if (/\.{2,}|。{2,}|……|…/.test(t)) scores.sad += 0.5;
  if (/!{1,}/.test(t) && scores.angry > 0) scores.angry += 0.3;
  if (/\?{1,}/.test(t) && scores.surprised > 0) scores.surprised += 0.2;

  const order = ['happy', 'sad', 'angry', 'surprised', 'shy'];
  let best = null, bestScore = 0;
  for (const k of order) {
    if (scores[k] > bestScore) { bestScore = scores[k]; best = k; }
  }
  if (!best) {
    return {
      emotion: 'neutral',
      action:  null,
      reply:   _reactRandomPick([
        '嗯嗯，我喺度聽緊。',
        '我聽緊你講，你繼續。',
        '收到，我喺度。',
      ]),
    };
  }
  const replyMap = {
    happy:     { emotion: 'happy',     action: 'mc', reply: _reactRandomPick(REPLY_POOL.correct.concat(REPLY_POOL.happy)) },
    sad:       { emotion: 'sad',       action: null, reply: _reactRandomPick(REPLY_POOL.sad.concat(REPLY_POOL.wrong)) },
    angry:     { emotion: 'angry',     action: null, reply: _reactRandomPick(REPLY_POOL.angry) },
    shy:       { emotion: 'shy',       action: null, reply: _reactRandomPick(REPLY_POOL.shy) },
    surprised: { emotion: 'surprised', action: null, reply: _reactRandomPick(REPLY_POOL.surprised) },
  };
  return replyMap[best];
}

const T = function(name, text, expect) {
  const r = _reactKeyword(text);
  const ok = r.emotion === expect;
  const mark = ok ? 'PASS' : 'FAIL';
  console.log(mark + ' ' + name + ' [' + text + '] => ' + r.emotion + (ok ? '' : ' (expected ' + expect + ')') + ' | reply: ' + r.reply);
  if (!ok) process.exit(1);
};

T('T1',  '我答啱咗！', 'happy');
T('T2',  '今日好慘呀', 'sad');
T('T3',  '我好嬲呀', 'angry');
T('T4',  '我害羞', 'shy');
T('T5',  '嘩！', 'surprised');
T('T6',  'Hello', 'neutral');
T('T7',  '我今日好累', 'sad');
T('T8',  '我好開心！', 'happy');
T('T9',  '點解會咁????', 'surprised');
T('T10', '唉...', 'sad');
T('T11', '我覺得不舒服', 'sad');
T('T12', '我好興奮', 'happy');
T('T13', '我討厭佢', 'angry');
T('T14', '今天好難受', 'sad');
T('T15', '我好寂寞', 'sad');
T('T16', 'love this', 'happy');
T('T17', 'amazing day', 'happy');
T('T18', 'cry cry', 'sad');
T('T19', 'furious!!!', 'angry');
T('T20', 'asdf qwer zxcv lorem ipsum', 'neutral');
T('T21', '好嬲呀!!!', 'angry');
T('T22', '我好驚', 'surprised');
T('T23', '今天很開心', 'happy');
T('T24', '我失戀了', 'sad');
T('T25', '真係嬲到爆', 'angry');

console.log('');
console.log('=== ALL 25 KEYWORD TESTS PASSED ===');
