class Capital:
    def __init__(self, initialBalance: float):
        self.currentBalance = initialBalance
        self.monthlyIncome = 0.0
        self.monthlyExpenses = 0.0
        self.isBankrupt = False
    
    def addFunds(self, amount: float):
        if amount > 0:
            self.currentBalance += amount
    
    def deductFunds(self, amount: float) -> bool:
        if 0 < amount <= self.currentBalance:
            self.currentBalance -= amount
            return True
        return False
    
    def updateMonthlyBudget(self):
        self.currentBalance += self.monthlyIncome
        self.currentBalance -= self.monthlyExpenses
        self.checkBankruptcy()
    
    def checkBankruptcy(self) -> bool:
        self.isBankrupt = self.currentBalance <= 0
        return self.isBankrupt
    
    def getBalance(self) -> float:
        return self.currentBalance
    
    def setIncome(self, income: float):
        if income >= 0:
            self.monthlyIncome = income
    
    def setExpenses(self, expenses: float):
        if expenses >= 0:
            self.monthlyExpenses = expenses
