---
type: insight
title: Metacognition, Obsidian, and AI Agents
description: How personal metacognition, Obsidian, and AI agent workflows connect into a practical memory and execution layer.
created: 2026-06-02
updated: 2026-06-02 23:03
---
# Metacognition, Obsidian, and AI Agents

- I thought I was just using Obsidian to give my AI agents more context. But I eventually realized I was building something deeper: a metacognitive layer. A system that lets my agents remember, self-correct, follow operating principles, and improve over time.

- I watched a video on youtube the other day about animals and if they have a sense of self. The video walked through multiple experiments. The first showed animals looking at themselves through a mirror with something unusual the experimenters put on their face. These animals were then put in front of a mirror and tested to see their own reactions. Some would realize it was their own face and would try to remove it or do something about it. Others such as dogs or cats would bark or meow at it thinking it was another animal. Originally scientists believed the animals who realized it was their own face with a new mark had a sense of self while those who didn’t notice did not have a sense of self. This was faulty reasoning. So the next experiment was more catered to the animals’ senses, i.e. sense of smell, echolocation, touch, etc. When animals were tested based off their perception of reality more animals appeared capable of detecting changes related to themselves.

- This was intriguing because this suggested that self-recognition may look different across species depending on their dominant sensory systems. Although they may interpret it differently by species they all could notice shifts in their own unique makeup. The youtube video explored further and the second experiment involved each animals’ knowledge and their ability to comprehend their capabilities and knowledge. Animals would be rewarded with treats based off answering questions, some questions were easier than others and the animals had the ability to choose which questions they had to answer. Many chose questions they were more **confident** in. This was the most interesting part of the video because THIS displayed metacognition in animals.

> Metacognition: thinking about your own thinking.

- Growing up I’ve always been a deep thinker. I think about my own thoughts, my feelings, why I think certain ways, my beliefs, other’s beliefs, why others would think certain ways, how people react to things I say, how I react to others, the list goes on. I never understood why, others would say this was over thinking. As I got older and started reading more I started realizing that this was described as high metacognition. High metacognition can become overthinking when it is unmanaged. But when controlled, it becomes a system for self-regulation.

- I realized by thinking deeply about my body’s incentive systems; dopamine, interests, laziness, and wants, that I could gamify my body and mind. High metacognition allowed me to see my weaknesses but also my strengths. An example of this was that I’ve always wanted to stay fit in my life, in college I gamified this but setting hard to reach goals such as benching 3 plates, rock climbing, standard progressive overload lifting programs. This gamified staying fit by chasing arbitrary numbers and weights. Working towards those goals would inevitably make me fit as I progressed. I realized this was the key in any aspect of life. If I wanted abs I found the sport where I saw most people had abs: rock climbing, if I wanted to make more money I would work towards the industry where people made a lot of money: tech, if I wanted to have a more balanced life forcing me to sleep and walk: own dog breeds that were high maintenance.

- Having high metacognition feels like a superpower. I could combine things I was naturally drawn to and add incentives to create a structure that would inevitably help me reach goals that were aligned with those incentives.

- Thinking about the evolution of LLMs from a user perspective, I realized that it was similar to cognitive evolution. We had words/language, culture, tool use and metacognition. LLMs began as systems trained to predict language across massive text and code datasets. At first, they looked like chatbots. But underneath, they had learned compressed patterns of human knowledge, culture, reasoning, and communication. Now we are seeing tool use. With AI apps and agents, LLMs are able to connect through CLIs, MCPs, APIs, scripts, queries, context vaults. I believe the next unlock is AI metacognition.

- As AI agents scale, there needs to be a system that understands its own weaknesses, its own biases, whether it can efficiently figure things out from its own model, how to manage itself. I think reasoning is one of the first steps to this process.

- But in addition to reasoning, I discovered a practical way to develop something like a prefrontal cortex for LLMs. That is with Obsidian. Interestingly I wrote the first half of this thought post unknowingly realizing that I had accidentally built a small, practical version of this missing layer. I stashed this in the back of my mind and out of nowhere it all clicked.

- Ever since the frontier models hit a step function jump in advancement in early 2026, I’ve been using the models alongside Obsidian. Obsidian is just a nice UI for markdown files. I believed it was originally created for note-taking. It still is used for note-taking and organization of markdown files/folders actually. But people realized that agents work really well with markdown files. I think it’s because they were trained on so many GitHub repos where people stored a lot of great context within markdown files whether it was about their codebase, projects, or whatever they wanted to write about. I’m not sure whether that is true but that’s just a hunch. So I went ahead and used that philosophy to store context about my life.

- I’ve always had a fascination for logging my thoughts, stats, and memories down. I used to use Notion for this but found it kinda clunky and always dreamed of a better automated and simplified but customizable way to log my life so that I could draw analytics and conclusions. With AI agents and Obsidian I realized the day was finally here and I could finally create workflows that I only dreamed of before. For example I’ve created iPhone automations where I could just swipe down and click a widget which will open a text box for me to write random thoughts, jot down stats, or instruct my agent to do a task. This random note gets appended to an Obsidian file and later on gets read, organized, executed, etc by a scheduled agent that reads through it on a recurring basis (I set to every 3 hours). This helps me because my mind jumps a lot throughout the day and I have thoughts that come and go. I never had places to put it but now I can just do brain dumps throughout the day and have my agent automatically organize it.

- I use a similar structure for professional projects too. The pattern is the same: daily notes, reusable workflows, project context, session logs, and operating principles. I didn’t know it before starting this thought post, but I was basically creating a metacognitive layer for my agents, which was actually an extension of my own metacognition.

- My agents are becoming extensions of my own metacognitive process. This is how I scaffold it.

- I always start off with 3 important folders
     - 00_inbox
         - quick captures/braindumps/agent research with no folder
     - 01_daily
         - daily notes labeled `YYYY-MM-DD`
     - 05_skills
         - skills folders for any recurring task

- Then as I start doing brain dumps and writing daily notes I create 10_projects folder that holds different domains/projects that are recurring and need its own space

- For agent workflows and ”AI metacognition” I add an AGENTS.md file that acts as an operating manual/index to different skills, guardrails, etc. This file is the first file that gets loaded into an agent’s context window when opening the agent in your vault.

- Then I set up a SESSION_LOGS.md and a SESSIONS_LOGS.db. The markdown version has a quick 7 day summary of session logs and the .db is a sqlite database that gets inserted with a summary row and timestamp after every agent interaction. I used to have everything in one long markdown until I realized how inefficient that was and that it broke my Obsidian app. Now I have a set of skills that inserts, reads, queries, audits the database.

- I then have a set of automations that make my agents housekeep, organize, review, research, send me newsletters, etc with all the context I build up in this vault. I also make sure to save any troubleshooting to have a recursive learning loop.

- I think this is the next step in AI. This is why tools like OpenClaw, Hermes Agent, and Garry Tan’s gbrain feel like part of the same wave: people are trying to build persistent agent systems with memory, skills, context, and execution. I guess what I am saying is I did not make any revolutionary discovery but I was able to piece together the solution to a bottleneck that I am sure many people are experiencing with AI. This is basically building out that execution layer when referencing back to my other post [[blog/tech_layoffs_ai_restructuring|Layoffs, the two levers, AI]].
