// hooks/useTranslation.js

export const useTranslation = () => {
  const translateMyMemory = async (text, source, target) => {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(
      text
    )}&langpair=${source}|${target}`;
    const response = await fetch(url);
    const data = await response.json();
    return data.responseData ? data.responseData.translatedText : null;
  };

  const translateDeepL = async (text, source, target, key) => {
    if (!key) throw new Error('DeepL API Key required');

    const mapLang = l => {
      if (l === 'eng') return 'EN';
      if (l === 'por') return 'PT-BR';
      if (l === 'spa') return 'ES';
      if (l === 'fra') return 'FR';
      if (l === 'deu') return 'DE';
      if (l === 'jpn') return 'JA';
      return l.toUpperCase().slice(0, 2);
    };

    const targetCode = mapLang(target);
    const sourceCode = mapLang(source);

    const isFree = key.endsWith(':fx');
    const endpoint = isFree
      ? 'https://api-free.deepl.com/v2/translate'
      : 'https://api.deepl.com/v2/translate';

    const params = new URLSearchParams();
    params.append('text', text);
    params.append('target_lang', targetCode);
    params.append('source_lang', sourceCode);

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `DeepL-Auth-Key ${key}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.message || 'DeepL Error');
    }

    const data = await response.json();
    return data.translations && data.translations[0]
      ? data.translations[0].text
      : null;
  };

  return {
    translateMyMemory,
    translateDeepL,
  };
};
