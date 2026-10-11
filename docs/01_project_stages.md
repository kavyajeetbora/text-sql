# Text-to-SQL Project Plan

## Stack

| Piece | Choice | Why |
|---|---|---|
| Language | Python with `uv` | Matches your current setup |
| Database | SQLite first, DuckDB later | SQLite is zero-setup. DuckDB is what your real work uses, so the move is a small step. |
| LLM | Amazon Nova Micro or Claude Haiku on AWS Bedrock, via the `converse` API in `boto3` | Both are cheap and good enough for SQL generation. Converse gives one interface for any model, so you can swap models later. |
| Embeddings | Amazon Titan Text Embeddings V2 | Cheap, and you only need it from Stage 4 |
| Vector store | ChromaDB (local) | You already know it |

**Cost note:** Bedrock is pay-per-token and not part of the always-free tier. This project costs cents, but set a **$5 AWS Budget alert** on day one. You also have to enable model access in the Bedrock console for your region.

## Stages

**Stage 0: Ecosystem setup**
- Create the `uv` project and install `boto3`, `chromadb` and `python-dotenv`.
- Create an IAM user with Bedrock permissions, configure the AWS CLI and set the budget alert.
- Enable model access in Bedrock.
- Check that one hello-world `converse` call works.
- Check that one Titan embedding call returns a vector.

**Stage 1: Data and single-table queries (no joins)**
- Create the database with `customers`, `orders`, `products` and `sales`, and seed it with fake data using Faker or a short script.
- Start with the `orders` table only. Paste its `CREATE TABLE` statement into the prompt, add the user question, and have the model return SQL only.
- Run the SQL and print the result.
- Try questions like "total revenue in 2025", "top 5 orders by amount" and "orders per month".

**Stage 2: Make it safe and reliable**
- Strip markdown fences and explanation text from the model output.
- Allow SELECT only, and parse the SQL with `sqlglot` before running it.
- Add a row limit and open the database read-only.
- Learn which prompt wording gives stable output, such as temperature 0 and a strict system prompt.

**Stage 3: Multiple tables and joins**
- Give the prompt the full schema with foreign keys, plus 2-3 example rows per table.
- Ask for joins, group-bys and subqueries, and note where the model fails.
- Add column descriptions and a small business glossary ("revenue = quantity × unit_price", "active customer = ordered in the last 90 days").

**Stage 4: Schema retrieval with embeddings (schema linking)**
- Grow the schema to 15-20 tables.
- Embed each table's description and columns into ChromaDB.
- Retrieve only the top-k relevant tables per question, and send just those to the LLM.
- Compare accuracy and token cost against sending the whole schema.

**Stage 5: Self-correction loop**
- When the SQL errors, send the error message back to the LLM and retry up to 2 times.
- Log every attempt so you can see which errors recur.

**Stage 6: Few-shot retrieval**
- Store verified (question, SQL) pairs in ChromaDB.
- Retrieve the 3 most similar pairs and add them to the prompt.
- Watch how much accuracy improves.

**Stage 7: Evaluation**
- Write a test set of about 30 questions with gold SQL, graded easy, medium and hard.
- Score the results with execution accuracy (does the result match?) rather than exact SQL match.
- Use this to compare each stage and prompt change with numbers instead of guesses.

**Stage 8: Real-world hardening**
- Handle ambiguous questions by asking a clarifying question.
- Add conversation memory for follow-ups ("now filter that for Delhi").
- Add result explanation in plain English.
- Move to DuckDB and Parquet, as in your dashboard.
- Wrap it in a Flask API, then add a small UI.
- Add logging, cost tracking and a prompt-injection check.
- Optionally try LangGraph for the retry loop. This links to the agent module.

## Project structure
```
text2sql/
  pyproject.toml
  .env
  data/            # seed script + db file
  src/
    llm.py         # bedrock client
    schema.py      # schema loading / retrieval
    generate.py    # prompt + SQL generation
    guard.py       # validation
    run.py         # execute + retry loop
  eval/
    questions.json
    evaluate.py
```

## How we'll work
- You write the code at each stage. I explain the concept first, give you the goal and hints, and review what you paste.
- Each stage ends with a short check where you explain it back to me, so it also counts as interview prep.
- Don't move on until the stage works for you. A broken Stage 2 makes Stage 5 painful.

Shall we start at Stage 0? Tell me your AWS region and whether the CLI is already configured.