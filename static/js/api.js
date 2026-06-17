// Reactive API functions extracted from index.html
function getWidgetIframe() {
  // Try to find the widget iframe
  const iframe = document.querySelector('iframe[src*="widget"]');
  return iframe;
}

function sendDiary() {
  const input = document.getElementById("diary-input");
  const text = input.value.trim();
  if (!text) return;

  const iframe = getWidgetIframe();
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({
      type: "diary",
      payload: { content: text }
    }, "*");
    input.value = "";
  } else {
    alert(TRANSLATIONS[currentLang]["api.diary"] + ": Widget not found. Please load the widget first.");
  }
}

function sendQuiz(type) {
  const iframe = getWidgetIframe();
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({
      type: "quiz",
      payload: { subject: type }
    }, "*");
  } else {
    alert(TRANSLATIONS[currentLang]["api.quiz"] + ": Widget not found. Please load the widget first.");
  }
}

function sendReset() {
  const iframe = getWidgetIframe();
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({
      type: "reset",
      payload: {}
    }, "*");
  } else {
    alert(TRANSLATIONS[currentLang]["api.reset"] + ": Widget not found. Please load the widget first.");
  }
}
