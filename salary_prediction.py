import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score


print("Loading Dataset...")
df = pd.read_csv("expected_ctc.csv")

print("\nFirst 5 rows:")
print(df.head())

print("\nDataset Info:")
print(df.info())

print("\nChecking Missing Values:")
print(df.isnull().sum())

df = df.drop_duplicates()
df = df.dropna()
print("\nData cleaned successfully.")


# ------------------ Visualization ------------------

plt.figure()
sns.histplot(df["Expected_CTC"], kde=True)
plt.title("Salary Distribution")
plt.savefig("salary_distribution.png")
plt.show(block=False)
plt.pause(2)
plt.close()

plt.figure()
sns.boxplot(x=df["Expected_CTC"])
plt.title("Salary Boxplot")
plt.savefig("salary_boxplot.png")
plt.show(block=False)
plt.pause(2)
plt.close()

plt.figure(figsize=(10,8))
sns.heatmap(df.corr(), annot=True, cmap="coolwarm")
plt.title("Correlation Heatmap")
plt.savefig("correlation_heatmap.png")
plt.show(block=False)
plt.pause(2)
plt.close()


# ------------------ Feature / Target ------------------

X = df.drop("Expected_CTC", axis=1)
y = df["Expected_CTC"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\nTrain Test Split Done")


# ------------------ Models ------------------

lr = LinearRegression()
lr.fit(X_train, y_train)
pred_lr = lr.predict(X_test)
r2_lr = r2_score(y_test, pred_lr)

dt = DecisionTreeRegressor(random_state=42)
dt.fit(X_train, y_train)
pred_dt = dt.predict(X_test)
r2_dt = r2_score(y_test, pred_dt)

rf = RandomForestRegressor(n_estimators=200, random_state=42)
rf.fit(X_train, y_train)
pred_rf = rf.predict(X_test)
r2_rf = r2_score(y_test, pred_rf)


print("\nLinear Regression R2:", r2_lr)
print("Decision Tree R2:", r2_dt)
print("Random Forest R2:", r2_rf)


# ------------------ Cross Validation (ADVANCED) ------------------

cv_score = cross_val_score(rf, X, y, cv=5)
print("\nRandom Forest Cross Validation Score:", cv_score.mean())


# ------------------ Model Comparison Graph ------------------

models = ["Linear", "DecisionTree", "RandomForest"]
scores = [r2_lr, r2_dt, r2_rf]

plt.figure()
plt.bar(models, scores)
plt.title("Model Accuracy Comparison")
plt.ylabel("R2 Score")
plt.savefig("model_comparison.png")
plt.show(block=False)
plt.pause(2)
plt.close()

# ------------------ Feature Importance ------------------

importance = rf.feature_importances_

feature_df = pd.DataFrame({
    "Feature": X.columns,
    "Importance": importance
}).sort_values(by="Importance", ascending=False)

plt.figure(figsize=(8,5))
sns.barplot(x="Importance", y="Feature", data=feature_df)
plt.title("Feature Importance")
plt.savefig("feature_importance.png")
plt.show(block=False)
plt.pause(2)
plt.close()


# ------------------ Save Model ------------------

pickle.dump(rf, open("salary_model.pkl", "wb"))
print("\nModel Saved Successfully")


# ------------------ Real Time Prediction ------------------

print("\n====== Salary Prediction System ======")

exp = float(input("Enter Experience: "))
test = float(input("Enter Test Score: "))
interview = float(input("Enter Interview Score: "))

prediction = rf.predict([[exp, test, interview]])

print("\nPredicted Expected CTC:", prediction[0])