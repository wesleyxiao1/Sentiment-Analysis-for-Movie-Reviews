import datetime
print(datetime.datetime.now().time())

import torch
from torchtext import data

SEED = 1234

torch.manual_seed(SEED)
torch.cuda.manual_seed(SEED)
torch.backends.cudnn.deterministic = True



"""
TEXT = data.Field(tokenize='spacy')
LABEL = data.LabelField(dtype=torch.float)

from torchtext import datasets

#import pdb; pdb.set_trace()
print(f"loading IMDB dataset", datetime.datetime.now().time())
train_data, test_data = datasets.IMDB.splits(TEXT, LABEL)
print(f"finished loading IMDB dataset", datetime.datetime.now().time())

print(f'Number of training examples: {len(train_data)}')
print(f'Number of testing examples: {len(test_data)}')

print(vars(train_data.examples[0]))

import random
train_data, valid_data = train_data.split(random_state=random.seed(SEED))

print(f'Number of training examples: {len(train_data)}')
print(f'Number of validation examples: {len(valid_data)}')
print(f'Number of testing examples: {len(test_data)}')

TEXT.build_vocab(train_data, max_size=25000)
LABEL.build_vocab(train_data)

print(f"Unique tokens in TEXT vocabulary: {len(TEXT.vocab)}")
print(f"Unique tokens in LABEL vocabulary: {len(LABEL.vocab)}")

print(TEXT.vocab.freqs.most_common(20))
print(TEXT.vocab.itos[:10])
print(LABEL.vocab.stoi)
"""

BATCH_SIZE = 64

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
train_iterator, valid_iterator, test_iterator = data.BucketIterator.splits(
	(train_data, valid_data, test_data),
	batch_size=BATCH_SIZE,
	device=device)


import torch.nn as nn

class RNN(nn.Module):
	def __init__(self, input_dim, embedding_dim, hidden_dim, output_dim):
		super().__init__()

		self.embedding = nn.Embedding(input_dim, embedding_dim)
		self.rnn = nn.RNN(embedding_dim, hidden_dim)
		self.fc = nn.Linear(hidden_dim, output_dim)

	def forward(self, x):
		#x = [sent len, batch size]
		
		#embedded = [sent len, batch size, emb dim]
		embedded = self.embedding(x)

		#output = [sent len, batch size, hid dim]
		#hidden = [1, batch size, hid dim]
		output, hidden = self.rnn(embedded)

		assert torch.equal(output[-1,:,:], hidden.squeeze(0))

		return self.fc(hidden.squeeze(0))


INPUT_DIM = len(TEXT.vocab)
EMBEDDING_DIM = 100
HIDDEN_DIM  = 256
OUTPUT_DIM = 1

model = RNN(INPUT_DIM, EMBEDDING_DIM, HIDDEN_DIM, OUTPUT_DIM)

import torch.optim as optim
optimizer = optim.SGD(model.parameters(), lr=0.001)

criterion = nn.BCEWithLogitsLoss()
model = model.to(device)
criterion = criterion.to(device)

def binary_accuracy(preds, y):
	# returns accuracy per batch

	#round prediction to the closest integer
	rounded_preds = torch.round(torch.sigmoid(preds))
	correct = (rounded_preds == y).float() #convert into float for division
	acc = correct.sum()/len(correct)
	return acc

def train(model, iterator, optimizer, criterion):
	epoch_loss = 0
	epoch_acc = 0

	model.train()
	for batch in iterator:
		optimizer.zero_grad()

		predictions = model(batch.text).squeeze(1)
		loss = criterion(predictions, batch.label)
		acc = binary_accuracy(predictions, batch.label)

		loss.backward()
		optimizer.step()

		epoch_loss += loss.item()
		epoch_acc += acc.item()

	return epoch_loss / len(iterator), epoch_acc / len(iterator)

def evaluate(model, iterator, criterion):
	epoch_loss = 0
	epoch_acc = 0

	model.eval()
	with torch.no_grad():
		for batch in iterator:
			predictions = model(batch.text).squeeze(1)
			loss = criterion(predictions, batch.label)
			acc = binary_accuracy(predictions, batch.label)

			epoch_loss += loss.item()
			epoch_acc += acc.item()

	return epoch_loss / len(iterator), epoch_acc / len(iterator)

N_EPOCHS = 5
for epoch in range(N_EPOCHS):
	train_loss, train_acc = train(model, train_iterator, optimizer, criterion)
	valid_loss, valid_acc = evaluate(model, valid_iterator, criterion)
	print(f'| Epoch: {epoch+1:02} | Train Loss: {train_loss:.3f} | Train Acc: {train_acc*100:.2f}% | Val. Loss: {valid_loss:.3f} | Val. Acc: {valid_acc*100:.2f}% |')


test_loss, test_acc = evaluate(model, test_iterator, criterion)

print(f'| Test Loss: {test_loss:.3f} | Test Acc: {test_acc*100:.2f}% |')

print(datetime.datetime.now().time())




