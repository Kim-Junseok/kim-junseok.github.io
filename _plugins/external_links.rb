# frozen_string_literal: true

require 'uri'

module HomepageExternalLinks
  ANCHOR_PATTERN = /<a\b[^>]*>/i.freeze
  HREF_PATTERN = /\bhref\s*=\s*(['"])(.*?)\1/i.freeze
  REL_PATTERN = /\brel\s*=\s*(['"])(.*?)\1/i.freeze
  TARGET_PATTERN = /\btarget\s*=\s*(['"])(.*?)\1/i.freeze

  module_function

  def apply(html, site_host)
    html.gsub(ANCHOR_PATTERN) do |tag|
      href = tag.match(HREF_PATTERN)&.[](2)
      next tag unless external_href?(href, site_host)

      with_target = ensure_target_blank(tag)
      ensure_safe_rel(with_target)
    end
  end

  def external_href?(href, site_host)
    return false if href.nil? || href.empty?

    uri = URI.parse(href)
    return false unless %w[http https].include?(uri.scheme)

    site_host.nil? || uri.host != site_host
  rescue URI::InvalidURIError
    false
  end

  def ensure_target_blank(tag)
    if tag.match?(TARGET_PATTERN)
      tag.sub(TARGET_PATTERN, 'target="_blank"')
    else
      tag.sub(/>$/, ' target="_blank">')
    end
  end

  def ensure_safe_rel(tag)
    match = tag.match(REL_PATTERN)

    if match
      rel_values = match[2].split(/\s+/)
      %w[noopener noreferrer].each do |value|
        rel_values << value unless rel_values.include?(value)
      end

      tag.sub(REL_PATTERN, %(rel="#{rel_values.join(' ')}"))
    else
      tag.sub(/>$/, ' rel="noopener noreferrer">')
    end
  end
end

Jekyll::Hooks.register :site, :post_write do |site|
  site_host = URI.parse(site.config['url'].to_s).host
  html_files = Dir[File.join(site.dest, '**', '*.html')]

  html_files.each do |path|
    html = File.read(path, encoding: 'UTF-8')
    updated_html = HomepageExternalLinks.apply(html, site_host)
    File.write(path, updated_html) unless updated_html == html
  end
rescue URI::InvalidURIError
  Jekyll.logger.warn 'ExternalLinks:', 'Skipping external link rewrite because site.url is invalid.'
end
