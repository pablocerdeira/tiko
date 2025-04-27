# core/summarizer.py
from .extractor import Extractor
from .llm import LLM

class Summarizer:
    def summarize_text(self, text):
        """Generate summary for given text using fallback strategy to handle context window errors."""
        return self.summarize_chunk(text, self.chunk_word_threshold)

    def summarize_chunk(self, text, threshold):
        """Recursively summarize the text using a given word threshold. Reduces chunk size if needed."""
        min_threshold = 1000
        words = text.split()

        # If the text length is within the threshold, try summarizing directly
        if len(words) <= threshold:
            summary = self.llm.summarize(text)
            if summary is not None:
                return summary
            else:
                # If summarization fails, reduce threshold if possible and retry
                if threshold > min_threshold:
                    new_threshold = max(min_threshold, threshold // 2)
                    print(f"Reducing threshold from {threshold} to {new_threshold} and retrying...")
                    return self.summarize_chunk(text, new_threshold)
                else:
                    print("Minimum threshold reached; unable to summarize.")
                    return None

        # If text is longer than threshold, split it into chunks and summarize each chunk recursively
        chunks = [" ".join(words[i:i+threshold]) for i in range(0, len(words), threshold)]
        summaries = []
        for chunk in chunks:
            chunk_summary = self.summarize_chunk(chunk, threshold)
            if chunk_summary is None:
                print(f"Error summarizing a chunk with threshold {threshold}")
            else:
                summaries.append(chunk_summary)

        combined = "\n".join(summaries)
        # If the combined summary still exceeds the threshold, reduce threshold and try summarizing the combined text
        if len(combined.split()) > threshold:
            new_threshold = max(min_threshold, threshold // 2)
            print(f"Combined summary exceeds threshold; reducing threshold from {threshold} to {new_threshold} and summarizing combined text...")
            return self.summarize_chunk(combined, new_threshold)
        else:
            return combined
        
    def __init__(self, config):
        self.config = config
        self.extractor = Extractor(config)
        self.llm = LLM(config)
        self.chunk_word_threshold = config.get('summarizer', {}).get('chunk_word_threshold', 80000)

        # Setup llm_refiner if model_refiner is provided in the active provider configuration
        provider = self.llm.provider
        provider_cfg = config.get('llm', {}).get('providers', {}).get(provider, {})
        model_refiner = provider_cfg.get('model_refiner')
        if model_refiner:
            import copy
            config_refiner = copy.deepcopy(config)
            config_refiner['llm']['providers'][provider]['model'] = model_refiner
            self.llm_refiner = LLM(config_refiner)
        else:
            self.llm_refiner = None

    def summarize_file(self, file_path):
        """Extract text from file and generate a summary via LLM, handling long texts by chunking."""
        text = self.extractor.extract_text_from_file(file_path)
        if not text:
            return "Could not extract text from file."

        summary = self.summarize_text(text)

        if not summary:
            return "Could not generate summary."

        # Final step: if the summary is too long, re-submit for a final concise summary
        # Estimate that 1 token ≃ 0.75 words; final_word_limit = max_tokens * 0.75
        final_word_limit = int(self.llm.max_tokens * 0.75)
        words_summary = summary.split()
        if len(words_summary) > final_word_limit:
            prompt = ("From the summary below, produce a final summary that is cohesive and complete, including all relevant points, "
                      "names of main parties involved, and maintaining important details, preferably maintaining chronology, but eliminating repetitions and redundant or unnecessary information. "
                      "Summary: " + summary)
            if self.llm_refiner is not None:
                final_summary = self.llm_refiner.summarize(prompt)
            else:
                final_summary = self.llm.summarize(prompt)
            if final_summary:
                summary = final_summary

        return summary
