'use client';

import { motion } from 'framer-motion';
import { WELCOME_MESSAGE, WELCOME_DESCRIPTION } from '@/lib/constants';

export function WelcomeSection() {
  return (
    <motion.div
      className="flex flex-col"
      style={{ transition: "all 0.2s ease-out" }}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <h3 className="mb-2 text-center text-3xl font-medium">
        {WELCOME_MESSAGE}
      </h3>
      <div className="text-muted-foreground px-4 text-center text-lg">
        {WELCOME_DESCRIPTION}
      </div>
    </motion.div>
  );
} 