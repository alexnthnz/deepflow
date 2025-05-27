'use client';

import { motion } from 'framer-motion';
import { SAMPLE_QUESTIONS, ANIMATION_DELAYS } from '@/lib/constants';

interface QuestionCardsProps {
  onQuestionClick: (question: string) => void;
}

export function QuestionCards({ onQuestionClick }: QuestionCardsProps) {
  return (
    <ul className="flex flex-wrap">
      {SAMPLE_QUESTIONS.map((question, index) => (
        <motion.li
          key={question}
          className="flex w-1/2 shrink-0 p-2 active:scale-105"
          style={{ transition: "all 0.2s ease-out" }}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{
            duration: ANIMATION_DELAYS.DURATION,
            delay: index * ANIMATION_DELAYS.CARD_STAGGER + ANIMATION_DELAYS.INITIAL_DELAY,
            ease: "easeOut",
          }}
        >
          <div
            className="bg-card text-muted-foreground cursor-pointer rounded-2xl border px-4 py-4 opacity-75 transition-all duration-300 hover:opacity-100 hover:shadow-md"
            onClick={() => onQuestionClick(question)}
          >
            {question}
          </div>
        </motion.li>
      ))}
    </ul>
  );
} 