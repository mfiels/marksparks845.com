// Google Analytics, on the live site only. Taps on call, text, and email links are sent as
// events, tagged with where on the page the link was.
(function () {
  const ID = "G-8S321ND54R";
  if (!/(^|\.)marksparks845\.com$/.test(location.hostname)) return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    window.dataLayer.push(arguments);
  };
  gtag("js", new Date());
  gtag("config", ID);

  const script = document.createElement("script");
  script.async = true;
  script.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
  document.head.appendChild(script);

  const EVENTS = [
    ["tel:", "call_click"],
    ["sms:", "text_click"],
    ["mailto:", "email_click"],
  ];

  function placement(link) {
    if (link.closest("header")) return "header";
    if (link.closest("footer")) return "footer";
    const section = link.closest("section");
    return (section && (section.id || section.className)) || "page";
  }

  document.addEventListener("click", (e) => {
    const link = e.target.closest("a[href]");
    if (!link) return;
    const href = link.getAttribute("href");
    const match = EVENTS.find(([prefix]) => href.startsWith(prefix));
    if (match) gtag("event", match[1], { link_location: placement(link) });
  });
})();
