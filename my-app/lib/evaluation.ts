import { Passage } from './types';

export const samplePassage: Passage = {
  id: '1',
  title: 'The Secret Life of Honeybees',
  content: `Inside every beehive, there is a world more organized than most human cities. A single hive can contain up to 60,000 bees, and every single one has a job to do. At the center of the hive is the queen bee. She is the only bee that lays eggs—up to 2,000 per day during summer. Despite her title, the queen doesn't actually make decisions for the hive. Her main job is simply to lay eggs and keep the colony growing.

The worker bees are all female, and they do everything else. Young workers stay inside the hive, cleaning cells, feeding larvae, and building honeycomb from wax they produce from their own bodies. As they get older, they graduate to guarding the hive entrance. The oldest workers become foragers, flying up to five miles from the hive to collect nectar and pollen.

Male bees are called drones. They don't collect food, don't guard the hive, and don't have stingers. Their only purpose is to mate with queens from other hives. In autumn, when food becomes scarce, the workers push the drones out of the hive to conserve resources.

Bees communicate through dancing. When a forager finds a good source of flowers, she returns to the hive and performs a 'waggle dance' that tells other bees exactly where to find the food. The angle of her dance shows the direction relative to the sun, and the length of her waggle shows the distance.

This tiny insect has been making honey the same way for over 100 million years. Every spoonful of honey represents the life's work of about twelve bees.`,
  difficulty: 'medium'
};

// Hardcoded questions for evaluation (not dependent on the passage)
export const evaluationQuestions = {
  // Question 1: Fundamentals - tests basic grammar/vocabulary
  question1: {
    type: 'fundamentals',
    question: "Which sentence uses the correct form of the verb?\n\nA) The team have decided to postpone the meeting.\nB) The team has decided to postpone the meeting.\nC) The team are deciding to postpone the meeting.\nD) The team were decided to postpone the meeting.",
    correctAnswer: 'B',
    explanation: 'In American English, collective nouns like "team" typically take singular verbs.'
  },

  // Question 2: Understanding - tests inference from a short sentence
  question2: {
    type: 'understanding',
    question: 'Read this sentence and explain what it implies:\n\n"She smiled, but her eyes told a different story."\n\nWhat do you think this sentence suggests about the person being described?',
  },

  // Question 3: Interest - open-ended about reading preferences
  question3: {
    type: 'interest',
    question: 'What types of books or articles do you enjoy reading the most? What makes a piece of writing engaging for you personally?',
  },

  // Question 4: Comprehension - based on the honeybee passage
  question4: {
    type: 'comprehension',
    question: 'Based on the passage about honeybees, explain the social structure of a beehive. What are the different roles, and how does the division of labor change as bees age? Why do you think the author says the hive is "more organized than most human cities"?',
  }
};

export const firstQuestion = `Great! Now that you've read the passage, let's start with a simple question:

**What is this passage about?**

Please describe in your own words what the main topic of this passage is.`;
