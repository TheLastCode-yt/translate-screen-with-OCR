// hooks/useTranslation.js

const log = (message, data = null) => {
  const timestamp = new Date().toLocaleTimeString('pt-BR', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
  if (data) {
    console.log(`[${timestamp}] 🌐 Translation: ${message}`, data);
  } else {
    console.log(`[${timestamp}] 🌐 Translation: ${message}`);
  }
};

export const useTranslation = () => {
  const translateMyMemory = async (text, source, target) => {
    try {
      log(`Traduzindo com MyMemory: "${text}" (${source} → ${target})`);
      const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(
        text
      )}&langpair=${source}|${target}`;

      log('Enviando requisição para MyMemory API...');
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`MyMemory API error: ${response.status}`);
      }

      const data = await response.json();

      if (!data.responseData) {
        log('❌ MyMemory: Resposta inválida', data);
        return null;
      }

      const translated = data.responseData.translatedText;
      log(`✅ MyMemory: "${translated}"`, {
        qualidade: data.responseData.match || 0,
      });

      return translated;
    } catch (error) {
      log('❌ Erro MyMemory', error.message);
      throw error;
    }
  };

  const translateDeepL = async (text, source, target, key) => {
    try {
      if (!key) {
        log('❌ DeepL: Chave de API não fornecida');
        throw new Error('DeepL API Key required');
      }

      log(`Traduzindo com DeepL: "${text}" (${source} → ${target})`);

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
      log(`Códigos de idioma mapeados: ${sourceCode} → ${targetCode}`);

      const isFree = key.endsWith(':fx');
      const endpoint = isFree
        ? 'https://api-free.deepl.com/v2/translate'
        : 'https://api.deepl.com/v2/translate';

      log(`Usando endpoint DeepL: ${isFree ? 'FREE' : 'PRO'}`);

      const params = new URLSearchParams();
      params.append('text', text);
      params.append('target_lang', targetCode);
      params.append('source_lang', sourceCode);

      log('Enviando requisição para DeepL API...');
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Authorization: `DeepL-Auth-Key ${key}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: params,
      });

      if (!response.ok) {
        const error = await response.json();
        log('❌ Erro DeepL API', {
          status: response.status,
          mensagem: error.message,
        });
        throw new Error(error.message || `DeepL Error: ${response.status}`);
      }

      const data = await response.json();

      if (!data.translations || !data.translations[0]) {
        log('❌ DeepL: Resposta inválida', data);
        throw new Error('Invalid DeepL response');
      }

      const translated = data.translations[0].text;
      log(`✅ DeepL: "${translated}"`);

      return translated;
    } catch (error) {
      log('❌ Erro DeepL', error.message);
      throw error;
    }
  };

  return {
    translateMyMemory,
    translateDeepL,
  };
};
