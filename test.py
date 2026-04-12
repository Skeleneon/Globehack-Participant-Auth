import pickle

with open("previous_data.dat", "rb") as f:
    data = pickle.load(f)

print(type(data))   # should be <class 'set'>
print(len(data))
print(data)