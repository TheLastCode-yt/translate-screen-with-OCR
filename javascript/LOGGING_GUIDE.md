# 📋 Guia de Logs - Sistema de Tradução

## Visão Geral

A aplicação foi aprimorada com um sistema completo de logging para facilitar debug e monitoramento do pipeline de tradução. Todos os logs seguem um formato padronizado com **timestamps** e **emojis** para fácil identificação.

## Formato dos Logs

Todos os logs seguem este padrão:

```
[HH:MM:SS.mmm] emoji Módulo: mensagem
```

Exemplo:

```
[14:32:15.245] 📸 ImageProcessing: Inicializando preprocessamento...
[14:32:15.523] ✅ ImageProcessing: Canvas criado com dimensões 1024x768
```

## Emojis por Módulo

| Emoji | Módulo              | Função                                          |
| ----- | ------------------- | ----------------------------------------------- |
| 📸    | **ImageProcessing** | Captura e preprocessamento de imagem            |
| 🔤    | **OCR**             | Reconhecimento óptico de caracteres (Tesseract) |
| 🌐    | **Translation**     | Chamadas para APIs de tradução                  |
| 🚫    | **TextFilter**      | Validação e filtragem de texto                  |
| 📺    | **Pipeline**        | Orquestração geral do processo                  |

## Indicadores de Status

| Indicador | Significado                    |
| --------- | ------------------------------ |
| ✅        | Sucesso/Conclusão bem-sucedida |
| ❌        | Erro/Falha                     |
| ⚠️        | Aviso/Algo incomum             |
| ⏭️        | Passado/Ignorado               |
| 📍        | Ponto de informação importante |
| 🚀        | Início de processo major       |
| 📊        | Resumo/Estatísticas            |

## Fluxo de Logs Completo

### 1. **Início do Pipeline** (📺)

```
[HH:MM:SS.mmm] 📺 Pipeline: 🚀 Iniciando pipeline de tradução
  modo: 'crop'
  idioma_origem: 'Portuguese'
  idioma_destino: 'English'
  provedor: 'deepl'
```

### 2. **Captura de Tela** (📸)

```
[HH:MM:SS.mmm] 📸 ImageProcessing: Inicializando preprocessamento...
[HH:MM:SS.mmm] 📸 ImageProcessing: Canvas criado com dimensões: 1024x768
[HH:MM:SS.mmm] 📸 ImageProcessing: Dados de imagem extraídos
[HH:MM:SS.mmm] 📸 ImageProcessing: Análise de contraste: min=15, max=240
[HH:MM:SS.mmm] ✅ ImageProcessing: Preprocessamento concluído
```

### 3. **OCR** (🔤)

```
[HH:MM:SS.mmm] 🔤 OCR: Iniciando OCR...
[HH:MM:SS.mmm] 🔤 OCR: Worker criado para idioma: por
[HH:MM:SS.mmm] 🔤 OCR: Progresso: 25%
[HH:MM:SS.mmm] 🔤 OCR: Progresso: 50%
[HH:MM:SS.mmm] 🔤 OCR: Progresso: 75%
[HH:MM:SS.mmm] 🔤 OCR: Progresso: 100%
[HH:MM:SS.mmm] ✅ OCR: Reconhecimento concluído
  palavras_detectadas: 45
  linhas_detectadas: 8
  confianca_media: 92.5
  texto_preview: "Hello world, this is a..."
```

### 4. **Filtragem de Texto** (🚫)

```
[HH:MM:SS.mmm] 🚫 TextFilter: Texto muito curto
  texto: "Hi"
  comprimento: 2
  minimo: 3

[HH:MM:SS.mmm] ✅ TextFilter: Texto válido
  texto: "Hello world"
  comprimento: 11
```

### 5. **Tradução por Bloco** (🌐 + 📺)

```
[HH:MM:SS.mmm] 📺 Pipeline: 📍 Bloco 1: Traduzindo "Hello world..."...
[HH:MM:SS.mmm] 🌐 Translation: Traduzindo com DeepL: "Hello world" (eng → por)
[HH:MM:SS.mmm] 🌐 Translation: Códigos de idioma mapeados: EN → PT-BR
[HH:MM:SS.mmm] 🌐 Translation: Usando endpoint DeepL: PRO
[HH:MM:SS.mmm] 🌐 Translation: Enviando requisição para DeepL API...
[HH:MM:SS.mmm] ✅ DeepL: "Olá mundo"
[HH:MM:SS.mmm] ✅ Bloco 1 traduzido em 234ms
  original: "Hello world"
  traduzido: "Olá mundo"
```

### 6. **Resumo Final** (📺)

```
[HH:MM:SS.mmm] 📊 Pipeline: Resumo da tradução:
  tempo_total: 2341ms
  blocos_processados: 5
  blocos_traduzidos: 5
  taxa_sucesso: 100.0%
  tempo_capture: 145ms
  tempo_preprocess: 234ms
  tempo_ocr: 1234ms
```

## Casos de Erro

### Erro de Imagem

```
[HH:MM:SS.mmm] 📸 ImageProcessing: ❌ Erro ao processar imagem
  erro: "Canvas context not available"
```

### Erro de API DeepL

```
[HH:MM:SS.mmm] 🌐 Translation: ❌ Erro DeepL API
  status: 403
  mensagem: "Unauthorized"
```

### Erro no Pipeline

```
[HH:MM:SS.mmm] ❌ ERRO NO PIPELINE
  erro: "Tesseract Worker not initialized"
  tipo: "Error"
  tempo_total: 1234ms
  stack: "Error at recognizeText..."
```

## Monitoramento de Performance

Todos os logs incluem timestamps de alta precisão (até milissegundos). Use para:

1. **Identificar gargalos**: Qual etapa demora mais?
2. **Monitorar APIs**: Qual provedor é mais rápido?
3. **Rastrear erros**: Em qual etapa o erro ocorreu?

Exemplo de análise:

```
📸 Captura: 145ms
🎨 Processamento: 234ms
🔤 OCR: 1234ms (⚠️ bottleneck)
🌐 Tradução: 728ms (5 blocos)
───────────
Total: 2341ms
```

## Como Usar os Logs

### Console do VS Code (F12)

Pressione `F12` para abrir o DevTools e ver todos os logs em tempo real.

### Filtrando Logs no Console

```javascript
// No console, você pode filtrar por módulo:
// Logs de imagem
console.clear(); // limpa e rodá novamente focando em 📸

// Logs de OCR
console.clear(); // focando em 🔤

// Logs de API
console.clear(); // focando em 🌐
```

## Estrutura de Dados nos Logs

Alguns logs incluem objetos com dados úteis:

```javascript
// OCR Result
{
  palavras_detectadas: 45,
  linhas_detectadas: 8,
  confianca_media: 92.5,
  texto_preview: "..."
}

// Tradução
{
  original: "Hello world",
  traduzido: "Olá mundo",
  tempo_ms: 234
}

// Erro
{
  erro: "Message",
  tipo: "ErrorType",
  tempo_total: 1234,
  stack: "Error trace..."
}
```

## Dicas de Debug

1. **Procure por ❌ para encontrar erros rapidamente**
2. **Use Ctrl+F no console para buscar por emojis (ex: 🌐)**
3. **Anote os timestamps dos problemas para correlacionar com logs**
4. **Verifique o `tempo_total` para saber se é problema de timeout**
5. **Taxa de sucesso < 100% indica blocos filtrados - verifique 🚫 logs**

## Configuração

Os logs são gerados **automaticamente**. Não há configuração necessária.

Para **desabilitar** logs em produção, você pode descomentar as funções `log()` e adicionar uma flag:

```javascript
const isDev = process.env.NODE_ENV === 'development';

const log = (message, data = null) => {
  if (!isDev) return; // desabilita em produção
  // ... resto do código
};
```

## Exemplo de Sessão Completa

```
[14:32:15.100] 📺 Pipeline: 🚀 Iniciando pipeline de tradução
[14:32:15.245] 📸 ImageProcessing: Inicializando preprocessamento...
[14:32:15.523] ✅ ImageProcessing: Canvas criado com dimensões 1024x768
[14:32:15.750] 📸 ImageProcessing: Análise de contraste: min=15, max=240
[14:32:15.892] ✅ ImageProcessing: Preprocessamento concluído
[14:32:15.923] 🔤 OCR: Iniciando OCR...
[14:32:15.945] 🔤 OCR: Worker criado para idioma: por
[14:32:17.234] ✅ OCR: Reconhecimento concluído
[14:32:17.256] 📺 Pipeline: 📍 Bloco 1: Traduzindo "Hello world"...
[14:32:17.278] 🌐 Translation: Traduzindo com DeepL...
[14:32:17.512] ✅ DeepL: "Olá mundo"
[14:32:17.534] ✅ Bloco 1 traduzido em 256ms
[14:32:17.556] 📊 Pipeline: Resumo da tradução:
  tempo_total: 2456ms
  blocos_processados: 1
  blocos_traduzidos: 1
  taxa_sucesso: 100.0%
```

---

**Sistema de Logging Completo Implementado ✅**

Todos os módulos agora têm logging detalhado para facilitar debugging e análise de performance!
