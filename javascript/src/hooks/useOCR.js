// hooks/useOCR.js
import Tesseract from 'tesseract.js';
import { OCR_CONFIG } from '../utils/constants';

const log = (message, data = null) => {
  const timestamp = new Date().toLocaleTimeString('pt-BR', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
  if (data) {
    console.log(`[${timestamp}] 🔤 OCR: ${message}`, data);
  } else {
    console.log(`[${timestamp}] 🔤 OCR: ${message}`);
  }
};

export const useOCR = () => {
  // Cache do worker para reutilização
  let workerInstance = null;

  const getWorker = async language => {
    if (!workerInstance) {
      log(`Criando worker Tesseract para idioma: ${language}`);
      workerInstance = await Tesseract.createWorker(language, 1, {
        // Configurações de otimização
        tessedit_pageseg_mode: Tesseract.PSM.AUTO,
        tessedit_char_whitelist:
          'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789àáâãäåèéêëìíîïòóôõöùúûüçñÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÇÑ .,!?;:\'"()-',
      });
      log('✅ Worker criado com sucesso');
    }
    return workerInstance;
  };

  const terminateWorker = async () => {
    if (workerInstance) {
      log('Encerrando worker Tesseract');
      await workerInstance.terminate();
      workerInstance = null;
      log('✅ Worker encerrado');
    }
  };

  const filterWords = words => {
    return words.filter(word => {
      if (word.confidence < OCR_CONFIG.CONFIDENCE_THRESHOLD) return false;
      if (!word.text || word.text.trim().length < OCR_CONFIG.MIN_WORD_LENGTH)
        return false;
      if (word.bbox.x1 <= word.bbox.x0 || word.bbox.y1 <= word.bbox.y0)
        return false;

      const width = word.bbox.x1 - word.bbox.x0;
      const height = word.bbox.y1 - word.bbox.y0;
      if (width < OCR_CONFIG.MIN_WORD_SIZE || height < OCR_CONFIG.MIN_WORD_SIZE)
        return false;

      const aspectRatio = width / height;
      if (
        aspectRatio < OCR_CONFIG.ASPECT_RATIO_MIN ||
        aspectRatio > OCR_CONFIG.ASPECT_RATIO_MAX
      )
        return false;

      const text = word.text.trim();
      const charCount = new Set(text.toLowerCase()).size;
      const uniquenessRatio = charCount / text.length;
      if (uniquenessRatio < OCR_CONFIG.UNIQUENESS_RATIO_MIN) return false;

      if (!/[a-zA-Z0-9àáâãäåèéêëìíîïòóôõöùúûüçñ]/i.test(text)) return false;

      return true;
    });
  };

  // Algoritmo melhorado para agrupar palavras em frases
  const groupWords = words => {
    if (words.length === 0) return [];

    // Ordena palavras por posição (linha por linha, esquerda para direita)
    const sortedWords = [...words].sort((a, b) => {
      const yDiff = a.bbox.y0 - b.bbox.y0;
      if (Math.abs(yDiff) > 10) return yDiff; // Diferentes linhas
      return a.bbox.x0 - b.bbox.x0; // Mesma linha
    });

    const textBlocks = [];
    let currentBlock = null;

    for (let i = 0; i < sortedWords.length; i++) {
      const word = sortedWords[i];

      if (!currentBlock) {
        // Inicia novo bloco
        currentBlock = {
          words: [word],
          bbox: { ...word.bbox },
        };
      } else {
        const lastWord = currentBlock.words[currentBlock.words.length - 1];

        // Calcula distâncias
        const distanceX = word.bbox.x0 - lastWord.bbox.x1;
        const distanceY = Math.abs(word.bbox.y0 - lastWord.bbox.y0);

        // Altura média das palavras no bloco atual
        const avgHeight = currentBlock.bbox.y1 - currentBlock.bbox.y0;

        // Largura média dos espaços entre caracteres
        const avgWordWidth =
          (lastWord.bbox.x1 - lastWord.bbox.x0) /
          Math.max(lastWord.text.length, 1);
        const spaceThreshold = avgWordWidth * 1.5; // Espaço normal entre palavras
        const lineBreakThreshold = avgHeight * 0.5; // Tolerância para mesma linha

        // Critérios para continuar o bloco (mesma frase)
        const isSameLine = distanceY < lineBreakThreshold;
        const isNormalSpace = distanceX >= 0 && distanceX < spaceThreshold * 3;

        if (isSameLine && isNormalSpace) {
          // Adiciona palavra ao bloco atual
          currentBlock.words.push(word);
          currentBlock.bbox.x0 = Math.min(currentBlock.bbox.x0, word.bbox.x0);
          currentBlock.bbox.y0 = Math.min(currentBlock.bbox.y0, word.bbox.y0);
          currentBlock.bbox.x1 = Math.max(currentBlock.bbox.x1, word.bbox.x1);
          currentBlock.bbox.y1 = Math.max(currentBlock.bbox.y1, word.bbox.y1);
        } else {
          // Finaliza bloco atual e inicia novo
          textBlocks.push(currentBlock);
          currentBlock = {
            words: [word],
            bbox: { ...word.bbox },
          };
        }
      }
    }

    // Adiciona último bloco
    if (currentBlock) {
      textBlocks.push(currentBlock);
    }

    return textBlocks;
  };

  const extractTextBlocks = ocrResult => {
    let textBlocks = [];
    const words = filterWords(ocrResult.data.words);

    log(
      `Detectadas ${words.length} palavras com alta confiança (>${OCR_CONFIG.CONFIDENCE_THRESHOLD}% + filtros de qualidade)`
    );

    if (words.length > 0) {
      textBlocks = groupWords(words);
      log(
        `✅ Agrupadas em ${textBlocks.length} blocos de texto`,
        textBlocks.map(b => ({
          palavras: b.words.length,
          texto: b.words.map(w => w.text).join(' '),
        }))
      );
    } else {
      log(
        `⚠️ Detecção de palavras falhou, usando linhas. ${ocrResult.data.lines.length} linhas detectadas`
      );

      if (ocrResult.data.lines && ocrResult.data.lines.length > 0) {
        textBlocks = ocrResult.data.lines
          .filter(
            line =>
              line.confidence > OCR_CONFIG.LINE_CONFIDENCE_THRESHOLD &&
              line.text.trim().length > 0
          )
          .map(line => ({
            words: [],
            bbox: line.bbox,
            text: line.text.trim(),
          }));
        log(`Usando ${textBlocks.length} linhas como fallback`);
      }
    }

    return textBlocks;
  };

  const recognizeText = async (image, language, onProgress) => {
    try {
      log(`Iniciando reconhecimento de texto (idioma: ${language})`);
      const worker = await getWorker(language);

      log('Enviando imagem para Tesseract...');
      const result = await worker.recognize(image, {
        logger: m => {
          if (m.status === 'recognizing text' && onProgress) {
            const progress = Math.round(m.progress * 100);
            onProgress(progress);
            if (progress % 25 === 0 || progress === 100) {
              log(`Progresso OCR: ${progress}%`);
            }
          }
        },
      });

      log('✅ OCR concluído', {
        texto: result.data.text.substring(0, 100) + '...',
        palavrasDetectadas: result.data.words.length,
        linhasDetectadas: result.data.lines.length,
        confiança: result.data.confidence,
      });

      return result;
    } catch (error) {
      log('❌ Erro no OCR', error.message);
      throw error;
    }
  };

  return {
    recognizeText,
    extractTextBlocks,
    filterWords,
    groupWords,
    terminateWorker,
  };
};
