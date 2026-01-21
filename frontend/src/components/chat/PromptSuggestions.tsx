/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { promptSuggestionsStyles } from '../../styles/components';

export interface PromptSuggestion {
  id: string;
  text: string;
}

export interface PromptSuggestionsProps {
  prompts: PromptSuggestion[];
  loading: boolean;
  visible: boolean;
  onPromptClick: (text: string) => void;
}

export function PromptSuggestions({
  prompts,
  loading,
  visible,
  onPromptClick,
}: PromptSuggestionsProps) {
  if (!visible) return null;

  return (
    <div css={css(promptSuggestionsStyles.wrapper)}>
      {loading ? (
        <div css={css(promptSuggestionsStyles.loadingWrapper)}>
          <LoadingSpinner text="Generating suggestions..." />
        </div>
      ) : prompts.length > 0 ? (
        <div css={css(promptSuggestionsStyles.grid)}>
          {prompts.map(prompt => (
            <button
              key={prompt.id}
              onClick={() => onPromptClick(prompt.text)}
              css={css(promptSuggestionsStyles.buttonBase)}
            >
              {prompt.text}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
