# frozen_string_literal: true

module HomepageDefaultThemeMode
  MARKER = 'homepage-default-theme-mode'
  HTML_PATTERN = /<html\b[^>]*>/i.freeze
  DATA_MODE_PATTERN = /\sdata-mode\s*=\s*(['"]).*?\1/i.freeze

  module_function

  def apply(html, default_mode)
    with_mode = ensure_default_mode(html, default_mode)
    inject_boot_script(with_mode, default_mode)
  end

  def ensure_default_mode(html, default_mode)
    html.sub(HTML_PATTERN) do |tag|
      next tag.sub(DATA_MODE_PATTERN, %( data-mode="#{default_mode}")) if tag.match?(DATA_MODE_PATTERN)

      tag.sub(/>$/, %( data-mode="#{default_mode}">))
    end
  end

  def inject_boot_script(html, default_mode)
    return html if html.include?(MARKER)

    script = <<~HTML
      <script id="#{MARKER}">
        (function () {
          var html = document.documentElement;
          var defaultMode = '#{default_mode}';

          function readSession(key) {
            try {
              return sessionStorage.getItem(key);
            } catch (error) {
              return null;
            }
          }

          var preferredMode = readSession('theme-mode') || readSession('mode');

          if (preferredMode === 'light' || preferredMode === 'dark') {
            html.setAttribute('data-mode', preferredMode);
          } else if (preferredMode === 'auto') {
            html.removeAttribute('data-mode');
          } else {
            html.setAttribute('data-mode', defaultMode);
          }
        }());
      </script>
    HTML

    html.sub(/<head>/i, "<head>\n#{script}")
  end
end

Jekyll::Hooks.register :site, :post_write do |site|
  default_mode = site.config.fetch('default_theme_mode', 'dark').to_s
  default_mode = 'dark' unless %w[dark light].include?(default_mode)

  Dir[File.join(site.dest, '**', '*.html')].each do |path|
    html = File.read(path, encoding: 'UTF-8')
    updated_html = HomepageDefaultThemeMode.apply(html, default_mode)
    File.write(path, updated_html) unless updated_html == html
  end
end
