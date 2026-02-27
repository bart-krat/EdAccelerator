This repo i made up of both a Frontend which is the my-app folder and a backend in backend directory.

The decision to have two separate servers was made for the ability to scale out new features and have a clear separation of concerns.

**My-app**

The frontend in NextJS is primarily focused on the UI/UX. 

The session follows a linear structure.

First the student must read the passage, using a mouse hover over the text to ensure they read the whole piece. This not only ensures completion but gives a visual progress bar along with helping them focus on the sentence at hand. This code can be seen in the PassageDisplay.tsx.

This is in direct response to the user feedback of " it's annoying seeing the entire passage".

Once the User completes the reading then the actual teaching begins.

Without the Student knowing the structure is Evaluation -> Teach -> Quiz -> Review.

The transition between evaluation and teach is semi abstracted from the student so that don't feel they're under assessment. Under the phrasing of "tailoring the lesson to your needs" the student is asked some questions to evaluate their level. 

The evaluation is made up of 6 questions, the first 3 are designed to be semi personal and open-ended. The purpose is to get them talking about their views on the text and find out what is interesting to them.

The second 3 questions are randomly chosen from the batch of questions that generated at deployment.

These answers are then sent off to an llm to "evaluate" where a simple plan is given it will simply categorize their level as low, medium and high. And subsequently provide a teaching plan according to this level. One part that is getting assessed is the engagement of the user, if they are providing 1 word answers than a strong initiative will be to open up more.

The plan is provided to the teaching agent who will ask some questions and have an interactive conversation with the user, focusing on their needs. For the sake of the demo this has been limited to 5 questions.

At the end of this this teaching session the User will be Quizzed. This quiz will be based on their level as the original questions generated are in range from easy, medium, hard.

After this the User then gets to review the quiz and ask any further questions.




**Backend**

Because I wanted to keep a structured linear lesson, I have gone for an Orchestration architecture. 

in backend/api i have separates routes.py for all the endpoints to the frontend and schemas.py to include all the pydantic api contracts to ensure conistency of the data between boundaries.

The most important endpoint in routes.py is :

async def start_session(request: StartSessionRequest):

this will trigger the orchestrator : orch = create_orchestrator(session_id)

The orchestrator.py is the brain of the whole session.

The four phases of the session are broken in to sub modules : Evaluation, Teach, Quiz, Review. The central orchestration script uses a state object to move in between each phase and pass context to subsequent llm calls so that the progress of the student can be seen from beginning to end.

I began originally with more flexibility in the evaluation and teach stage working on an agent to work on a "While" loop until some desired result had been reached. However the agent weren't following the desired questions, behaviour to be asked or getting closer to their goal. 

Evaluator asked 3 pre-defined questions : what's the text about , is it non-ficiton or fiction, what did you like most.. And 3 random questions from the pool. I kept this deterministic as it was also more complex of juggle an evaluator llm producing two pieces of output one is the text that the user see's and two is the background evaluation. 

Therefore to constrain the behaviour the chat interface sets expectation with the user to ask 6 questions ( they don't need to know this is deterministic) and then bring the evaluation after this information has been captured.

More flexibility was allowed for the teach agent and this a genuine interaction between user and AI. And long term this is where focus on fine tuning can be made to improve the teaching component. As can be seen in the prompt the teacher takes the evaluation and level from the plan and works accordingly on the students needs.

The orchestrator allows this interaction to go for 5 questions and then a formal quiz is generated. Using the language of Quiz compared to Test is key as it makes it feel light however it is also necessary to measure progress and understanding. 