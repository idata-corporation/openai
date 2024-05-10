import os
from time import sleep
from openai import OpenAI
import json
import gradio as gr

client = OpenAI(
  #defaults to
  api_key = os.environ.get("OPENAI_API_KEY")
)

assistant = client.beta.assistants.create(
  name="Financial Analyst Assistant",
  instructions="You are an expert financial analyst. Use you knowledge base and the functions to answer questions about audited financial statements. Make sure you use data from the uploaded documents. Make sure you use the applied functions when applicable",
  model="gpt-4-turbo",
  tools=[{"type": "file_search"}]
)

debt_ratio_function = {
      "type": "function",
      "function": {
        "name": "debt_ratio",
        "description": "Calculate the debt ratio excluding mortgage backed securities (MBS) for a company, e.g. Freddie Mac",
        "parameters": {
          "type": "object",
          "properties": {
            "debt": {
              "type": "number",
              "description": "The total outstanding debt excluding mortgage backed securities (MBS) for a company, e.g. Freddie Mac"
            },
            "total_assets": {
              "type": "number",
              "description": "The total assets or total equity for a company, e.g. Freddie Mac"
            }
          },
          "required": ["debt", "total_assets"]
        }
      }
    }

cost_of_equity_function = {
      "type": "function",
      "function": {
        "name": "cost_of_equity",
        "description": "Calculate the cost of equity for a company",
        "parameters": {
          "type": "object",
          "properties": {
            "risk_free_rate": {
              "type": "number",
              "description": "The risk free rate for a company, e.g. Freddie Mac"
            },
            "beta": {
              "type": "number",
              "description": "The beta value for a company, e.g. Freddie Mac"
            },
            "market_return": {
              "type": "number",
              "description": "The beta value for a company, e.g. Freddie Mac"
            }
          },
          "required": ["risk_free_rate", "beta", "market_return"]
        }
      }
    }

marginal_tax_rate_function = {
      "type": "function",
      "function": {
        "name": "marginal_tax_rate",
        "description": "Calculate the marginal tax rate for a company",
        "parameters": {
          "type": "object",
          "properties": {
            "income_before_income_tax": {
              "type": "number",
              "description": "The income before income tax expense for a company, e.g. Freddie Mac"
            },
            "income_tax_expense": {
              "type": "number",
              "description": "The income tax expense for a company, e.g. Freddie Mac"
            }
          },
          "required": ["income_before_income_tax", "income_tax_expense"]
        }
      }
    }

wacc_function = {
      "type": "function",
      "function": {
        "name": "wacc",
        "description": "Calculate the weighted average cost of capital (WACC) for a company, e.g. Freddie Mac",
        "parameters": {
          "type": "object",
          "properties": {
            "debt_ratio": {
              "type": "number",
              "description": "The debt for a company, e.g. Freddie Mac"
            },
            "cost_of_debt_after_tax": {
              "type": "number",
              "description": "The cost of debt after tax for a company, e.g. Freddie Mac"
            },
            "equity_ratio": {
              "type": "number",
              "description": "The equity ratio for a company, e.g. Freddie Mac"
            },
            "cost_of_equity": {
              "type": "number",
              "description": "The cost of equity for a company, e.g. Freddie Mac"
            }
          },
          "required": ["debt_ratio", "cost_of_debt_after_tax", "equity_ratio", "cost_of_equity"]
        }
      }
    }

# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Financial Statements")
 
# Ready the files for upload to OpenAI
file_paths = ["./10ks/stats.txt", "./10ks/2023.pdf"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
 
# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.status)
print(file_batch.file_counts)

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tools=[debt_ratio_function, cost_of_equity_function, marginal_tax_rate_function, wacc_function, {"type": "file_search"}],
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
  temperature=0.1
)

# Recommended to create one thread per user as soon as the user initiates the conversation
thread = client.beta.threads.create()


# OpenAI functions
def debt_ratio(debt, total_assets):
  print("Function debt_ratio called, debt: ", debt, ", total_assets: ", total_assets)
  return (debt / total_assets)

def cost_of_equity(risk_free_rate, beta, market_return):
  print("Function cost_of_equity called, risk_free_rate: ", risk_free_rate, ", beta: ", beta, ", market_return: ", market_return)
  return (risk_free_rate + beta * (market_return - risk_free_rate))

def marginal_tax_rate(income_before_income_tax, income_tax_expense):
  print("Function marginal_tax_rate called, income_before_income_tax: ", income_before_income_tax, ", income_tax_expense: ", income_tax_expense)
  return (income_tax_expense / income_before_income_tax)

def wacc(debt_ratio, cost_of_debt_after_tax, equity_ratio, cost_of_equity):
  print("Function wacc called, debt_ratio: ", debt_ratio, ", cost_of_debt_after_tax: ", cost_of_debt_after_tax, 
        ", equity_ratio: ", equity_ratio, ", cost_of_equity: ", cost_of_equity)
  return (debt_ratio * cost_of_debt_after_tax + equity_ratio * cost_of_equity)

# Procedure to call OpenAI functions
def call_required_functions(required_actions):
  tool_outputs = []
  for action in required_actions["tool_calls"]:
    func_name = action['function']['name']
    arguments = json.loads(action['function']['arguments'])
    if func_name == "debt_ratio":
      output = debt_ratio(debt=arguments['debt'], total_assets=arguments['total_assets'])
      tool_outputs.append({
          "tool_call_id": action['id'],
          "output": str(output)
      })
    elif func_name == "cost_of_equity":
      output = cost_of_equity(risk_free_rate=arguments['risk_free_rate'], beta=arguments['beta'], 
                              market_return=arguments['market_return'])
      tool_outputs.append({
          "tool_call_id": action['id'],
          "output": str(output)
      })
    elif func_name == "marginal_tax_rate":
      output = marginal_tax_rate(income_before_income_tax=arguments['income_before_income_tax'], income_tax_expense=arguments['income_tax_expense'])
      tool_outputs.append({
          "tool_call_id": action['id'],
          "output": str(output)
      })
    elif func_name == "wacc":
      output = wacc(debt_ratio=arguments['debt_ratio'], cost_of_debt_after_tax=arguments['cost_of_debt_after_tax'], 
                    equity_ratio=arguments['equity_ratio'], cost_of_equity=arguments['cost_of_equity'])
      tool_outputs.append({
          "tool_call_id": action['id'],
          "output": str(output)
      })
    else:
      raise ValueError(f"Unknown function: {func_name}")
  return tool_outputs

# Loop for question input and processing
def ask_one_question(message, history):
  #user_input = input("What is your question? ")
  client.beta.threads.messages.create(
    thread_id = thread.id,
    role = "user",
    content = message
  )

  run = client.beta.threads.runs.create(
    thread_id = thread.id,
    assistant_id = assistant.id,
    instructions = "The user has a premium account."
  )

  print(run.status)
  while(run.status == "queued" or run.status == "in_progress" or run.status == "requires_action"):
    sleep(5)
    print("Waiting for the Assistant to respond...")
    run = client.beta.threads.runs.retrieve(
      thread_id = thread.id,
      run_id = run.id
    )
    print(run.status)
    #print(run.model_dump_json(indent=4))
    if run.status == "requires_action":
      print("Function calling...")
      tool_outputs = call_required_functions(run.required_action.submit_tool_outputs.model_dump())
      print("Submitting outputs back to the Assistant...")
      client.beta.threads.runs.submit_tool_outputs(
          thread_id=thread.id,
          run_id=run.id,
          tool_outputs=tool_outputs
      )

  messages = client.beta.threads.messages.list(
    thread_id = thread.id
  )

  # Loop through messages and print content based on role
  message_list = []
  for msg in messages.data:
    role = msg.role
    content = msg.content[0].text.value
    return f"{role.capitalize()}: {content}"
    #message_list += f"{role.capitalize()}: {content}"
    #print(f"{role.capitalize()}: {content}")
    #break




########################
# Ask questions
gr.ChatInterface(
    ask_one_question,
    chatbot=gr.Chatbot(height=800),
    textbox=gr.Textbox(placeholder="What is your question", container=False, scale=7),
    title="OpenAI with RAG and Function calling",
    description="Ask a question",
    theme="soft",
    retry_btn=None
).launch()

#while True:
#  ask_one_question(client, thread)