"""Scripts stealth inspirados no puppeteer-extra-plugin-stealth para Playwright."""

STEALTH_INIT_SCRIPT = """
(() => {
  const patch = (obj, prop, value) => {
    try {
      Object.defineProperty(obj, prop, { get: () => value });
    } catch (e) {}
  };

  patch(navigator, 'webdriver', undefined);
  patch(navigator, 'languages', ['pt-PT', 'pt', 'en-US', 'en']);
  patch(navigator, 'plugins', [1, 2, 3, 4, 5]);
  patch(navigator, 'hardwareConcurrency', 8);
  patch(navigator, 'deviceMemory', 8);

  if (!window.chrome) {
    window.chrome = { runtime: {}, loadTimes: () => ({}), csi: () => ({}) };
  }

  const originalQuery = window.navigator.permissions.query;
  window.navigator.permissions.query = (parameters) =>
  parameters.name === 'notifications'
    ? Promise.resolve({ state: Notification.permission })
    : originalQuery(parameters);

  const getParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter.call(this, parameter);
  };
})();
"""

CHROME_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-gpu",
    "--window-size=1366,768",
    "--lang=pt-PT",
]
