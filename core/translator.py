from deep_translator import GoogleTranslator, MyMemoryTranslator, DeeplTranslator
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time

class TranslationService:
    def __init__(self, config_manager):
        self.config = config_manager
        self._executor = ThreadPoolExecutor(max_workers=5)  # Parallel translation threads
    
    def translate_batch(self, texts, source_lang='auto', target_lang='en', provider=None):
        """
        Translate multiple texts in parallel for better performance.
        Returns a list of translated texts in the same order as input.
        """
        if not texts:
            return []
        
        if not provider:
            provider = self.config.get("default_provider", "mymemory")
        
        print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Tradução em lote: {len(texts)} textos ({source_lang} -> {target_lang})")
        
        # For small batches (1-2 texts), just translate sequentially
        if len(texts) <= 2:
            return [self.translate(t, source_lang, target_lang, provider) for t in texts]
        
        # For larger batches, use parallel translation
        results = [None] * len(texts)
        futures = {}
        
        for idx, text in enumerate(texts):
            future = self._executor.submit(
                self.translate, text, source_lang, target_lang, provider
            )
            futures[future] = idx
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Erro na tradução paralela: {e}")
                results[idx] = texts[idx]  # Fallback to original text
        
        return results

    def translate(self, text, source_lang='auto', target_lang='en', provider=None):
        if not text.strip():
            return ""

        if not provider:
            provider = self.config.get("default_provider", "mymemory")

        print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Traduzindo com {provider}: '{text[:50]}{'...' if len(text) > 50 else ''}' ({source_lang} -> {target_lang})")
        
        try:
            translate_start = time.time()
            
            if provider == "deepl":
                api_key = self.config.get_api_key("deepl")
                if not api_key:
                    print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] ERRO: DeepL API Key ausente")
                    return "Error: DeepL API Key missing."
                # DeepL from deep_translator
                translator = DeeplTranslator(api_key=api_key, source=source_lang, target=target_lang, use_free_api=True)
                result = translator.translate(text)
                translate_time = time.time() - translate_start
                print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] DeepL concluído em {translate_time:.2f}s")
                return result

            elif provider == "google":
                # User requested Cloud Translation API, but often users just want Google Translate.
                # Implementing the free version via deep_translator for simplicity and immediate usage,
                # as setting up Cloud API requires JSON credentials usually.
                # If an API key is provided, we could use the REST API directly.
                api_key = self.config.get_api_key("google")
                if api_key:
                    print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Usando Google Cloud API...")
                    # Simple REST API call for Google Cloud Translate with API Key
                    url = "https://translation.googleapis.com/language/translate/v2"
                    params = {
                        "q": text,
                        "source": source_lang if source_lang != 'auto' else None,
                        "target": target_lang,
                        "key": api_key
                    }
                    # Remove None values
                    params = {k: v for k, v in params.items() if v is not None}
                    
                    response = requests.post(url, params=params)
                    if response.status_code == 200:
                        result = response.json()['data']['translations'][0]['translatedText']
                        translate_time = time.time() - translate_start
                        print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Google Cloud API concluído em {translate_time:.2f}s")
                        return result
                    else:
                        error_msg = f"Error: Google API {response.text}"
                        print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] ERRO: {error_msg}")
                        return error_msg
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Usando Google Translate (gratuito)...")
                    result = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
                    translate_time = time.time() - translate_start
                    print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Google Translate concluído em {translate_time:.2f}s")
                    return result

            elif provider == "mymemory":
                # MyMemory requires specific language codes sometimes
                # Map common codes to what MyMemory likely expects if needed, or rely on standard ISO
                # The error suggests 'en' is not supported directly? 
                # Actually, MyMemory usually takes 'en', 'pt', etc.
                # But the error message lists 'english us': 'en-US', 'english uk': 'en-GB'.
                # It seems 'en' is ambiguous for MyMemory in deep_translator or the API.
                
                lang_map = {
                    'en': 'en-US',
                    'pt': 'pt-BR'
                }
                src = lang_map.get(source_lang, source_lang)
                tgt = lang_map.get(target_lang, target_lang)
                
                print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] Usando MyMemory ({src} -> {tgt})...")
                result = MyMemoryTranslator(source=src, target=tgt).translate(text)
                translate_time = time.time() - translate_start
                print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] MyMemory concluído em {translate_time:.2f}s")
                return result

            else:
                error_msg = f"Error: Unknown provider '{provider}'"
                print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] ERRO: {error_msg}")
                return error_msg

        except Exception as e:
            error_msg = f"Translation Error: {str(e)}"
            print(f"[{time.strftime('%H:%M:%S')}] [TRANSLATOR] EXCEÇÃO: {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
