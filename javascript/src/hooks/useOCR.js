// hooks/useOCR.js
import Tesseract from 'tesseract.js';
import { OCR_CONFIG } from '../utils/constants';

export const useOCR = () => {
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

  const groupWords = words => {
    const textBlocks = [];
    const processedWords = new Set();

    for (let i = 0; i < words.length; i++) {
      if (processedWords.has(i)) continue;

      const word = words[i];
      const block = {
        words: [word],
        bbox: { ...word.bbox },
      };

      for (let j = i + 1; j < words.length; j++) {
        if (processedWords.has(j)) continue;

        const otherWord = words[j];
        const distanceX = otherWord.bbox.x0 - block.bbox.x1;
        const distanceY = Math.abs(otherWord.bbox.y0 - block.bbox.y0);
        const avgHeight =
          (block.bbox.y1 -
            block.bbox.y0 +
            otherWord.bbox.y1 -
            otherWord.bbox.y0) /
          2;

        if (
          distanceY < avgHeight * 0.3 &&
          distanceX >= 0 &&
          distanceX < Math.max(avgHeight, 10)
        ) {
          block.words.push(otherWord);
          processedWords.add(j);
          block.bbox.x0 = Math.min(block.bbox.x0, otherWord.bbox.x0);
          block.bbox.y0 = Math.min(block.bbox.y0, otherWord.bbox.y0);
          block.bbox.x1 = Math.max(block.bbox.x1, otherWord.bbox.x1);
          block.bbox.y1 = Math.max(block.bbox.y1, otherWord.bbox.y1);
        }
      }

      processedWords.add(i);
      textBlocks.push(block);
    }

    return textBlocks;
  };

  const extractTextBlocks = ocrResult => {
    let textBlocks = [];
    const words = filterWords(ocrResult.data.words);

    console.log(
      `Detected ${words.length} words with high confidence (>${OCR_CONFIG.CONFIDENCE_THRESHOLD}% + quality filters)`
    );

    if (words.length > 0) {
      textBlocks = groupWords(words);
    } else {
      console.log(
        `Words detection failed, using lines instead. Detected ${ocrResult.data.lines.length} lines`
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
      }
    }

    return textBlocks;
  };

  const recognizeText = async (image, language, onProgress) => {
    const result = await Tesseract.recognize(image, language, {
      logger: m => {
        if (m.status === 'recognizing text' && onProgress) {
          onProgress(Math.round(m.progress * 100));
        }
      },
    });

    console.log('OCR Result:', result.data.text);
    console.log('Words:', result.data.words);
    console.log('Lines:', result.data.lines);

    return result;
  };

  return {
    recognizeText,
    extractTextBlocks,
    filterWords,
    groupWords,
  };
};
