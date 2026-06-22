# **AI Systems Interview Assignment**

## **Overview**

This interview is designed to evaluate how you approach building real-world AI systems under time constraints.

We are not looking for a polished or fully production-ready solution. We are looking at how you think, what you prioritize, how you scope an MVP, and how you turn an open-ended problem into something simple and working.

You are encouraged to explain your reasoning as you go, especially when making tradeoffs, simplifying scope, or deciding what not to build.

You may use any tools you want during the interview, including AI tools such as Claude, Codex, ChatGPT, or similar assistants.

What matters most is not whether you use AI tools, but how effectively and thoughtfully you use them.

## **What We’re Evaluating**

We are primarily evaluating:

* System design and ability to scope a sensible MVP  
* Ability to handle non-deterministic behavior in AI systems  
* Reliability and awareness of failure modes  
* Observability and debuggability  
* Clear reasoning and good engineering tradeoffs  
* Ability to build a small but working system quickly

## **Interview Structure**

Total time: 75–90 minutes

### **Part 1: System Design (30 minutes)**

Design a system where a user can provide a database connection, make natural language requests for charts and metrics, and iteratively build a custom dashboard on top of their own data.

Examples of requests might include:

* “Show weekly revenue by region”  
* “Create a chart of top customers by order volume”  
* “Add a metric for monthly active users”  
* “Break this down by product category”

#### **What to do**

* Start by defining a clear MVP  
* Walk through the core components of your system  
* Explain the key tradeoffs you are making  
* Keep the design simple and focused

#### **What we care about**

We are not looking for the most elaborate architecture. We are looking for clarity of thought, sensible scoping, and good judgment.

Focus on:

* What the minimum useful system is  
* How the system understands database schemas and metadata  
* How natural language requests become safe, executable queries  
* How the system chooses charts or metrics to create  
* How the system handles ambiguity, invalid requests, and failures  
* How you would make the system understandable and debuggable

## **Part 2: Build (45 minutes)**

Build a minimal working version of a core part of the system you designed.

#### **What to do** 

* Choose a small but meaningful slice of the system  
* Get something working end to end  
* Keep the scope tight  
* Talk through your decisions as you build when possible

#### **Guidance**

* You may use any programming language, framework, library, or AI tool  
* Working code matters more than perfect code  
* You do not need to build the full system  
* It is better to finish a narrow, functional slice than to start something broad and incomplete

Examples of reasonable slices include:

* Schema introspection plus natural language to SQL generation  
* A safe query generation and validation layer  
* Natural language to chart specification for a known schema  
* A simple dashboard editing loop that turns user requests into updated widgets

We prefer candidates who explain their thinking while building rather than only presenting a finished result at the end.

## **Final Discussion (10–15 minutes)**

Be prepared to discuss:

* What you would improve next  
* Where the system might fail  
* What you would change to productionize it  
* What tradeoffs you made due to time constraints

## **What We Care About Most**

We are looking for evidence that you can:

* Simplify an ambiguous problem  
* Make good decisions under time pressure  
* Build something runnable  
* Use AI tools effectively without blindly trusting them  
* Clearly explain your thinking and tradeoffs

## **What to Avoid**

Please avoid:

* Over-engineering  
* Spending too much time planning without building  
* Trying to solve too much  
* Not finishing something runnable  
* Blindly accepting code or ideas from AI tools without judgment

## **Expectations During the Interview**

A strong interview does not require a perfect solution.

A strong interview usually looks like this:

* You quickly identify a reasonable MVP  
* You keep the architecture simple  
* You choose a build scope that is achievable  
* You make tradeoffs explicitly  
* You get a meaningful slice working  
* You explain where the design is fragile or incomplete

## **Bottom Line**

This interview is about your ability to take an open-ended AI systems problem and turn it into a simple, working solution within limited time.

Prioritize clarity, speed, sound judgment, and execution.

