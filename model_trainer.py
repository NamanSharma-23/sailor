import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

df = pd.read_csv("project_training.csv")
x=df[["Days","Team_Size"]]
y=df["Actual_Cost"]
y_logic=df["On_Time"]

x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.2, random_state=42)
x_train_l, x_test_l, y_train_l, y_test_l = train_test_split(x,y_logic,train_size=0.4,random_state=42, stratify=y_logic)

model=LinearRegression()
model.fit(x_train,y_train)
prediction = model.predict(x_test)
error = mean_absolute_error(y_test, prediction)

print(f"Model Training Complete!")
print(f"On average, the AI's cost prediction is off by: ${error:.2f}")

logic_model=LogisticRegression()
logic_model.fit(x_train_l,y_train_l)
logic_preds = logic_model.predict(x_test_l)
score=accuracy_score(y_test_l, logic_preds)

print(f"On-Time Prediction Accuracy: {score * 100:.0f}%")