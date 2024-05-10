import os
from time import sleep
from openai import OpenAI

client = OpenAI(
  #defaults to
  api_key = os.environ.get("OPENAI_API_KEY")
)

# Upload a file with an "assistants" purpose
file = client.files.create(
	file=open("./10ks/2023.pdf", "rb"),
	purpose='assistants'
)

# Add the file to the assistant
assistant = client.beta.assistants.create(
	instructions="You are a financial advisor and a certified public accountant.  User your knowledge base to best respond to queries.",
	model="gpt-4-turbo",
	tools=[{"type": "retrieval"}],
	file_ids=[file.id]
)

# Recommended to create one thread per user as soon as the user initiates the conversation
thread = client.beta.threads.create()


def ask_one_question(client, thread):
	user_input = input("What is your question? ")
	message = client.beta.threads.messages.create(
		thread_id = thread.id,
		role = "user",
		content = user_input,
		file_ids = [file.id]
	)

	run = client.beta.threads.runs.create(
		thread_id = thread.id,
		assistant_id = assistant.id,
		instructions = "The user has a premium account."
	)

	print(run.status)
	while(run.status == "queued" or run.status == "in_progress"):
		sleep(1)
		print("Waiting for the Assistant to respond...")
		run = client.beta.threads.runs.retrieve(
			thread_id = thread.id,
			run_id = run.id
		)
		print(run.status)

	messages = client.beta.threads.messages.list(
		thread_id = thread.id
	)

	for m in messages:
		print(m.role + ": " + str(m.content[0].text))
		break

while True:
	ask_one_question(client, thread)
