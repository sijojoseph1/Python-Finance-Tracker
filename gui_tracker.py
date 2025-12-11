import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# --- 1. Database Setup and Functions (ഡാറ്റാബേസ് ഫംഗ്ഷനുകൾ) ---

DB_NAME = 'finance_tracker.db'

def connect_db():
    """SQLite ഡാറ്റാബേസിലേക്ക് കണക്റ്റ് ചെയ്യുന്നു."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def initialize_db():
    """Transactions ടേബിൾ ഉണ്ടാക്കുന്നു."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_transaction_to_db(type, amount, category, description=""):
    """പുതിയ ഇടപാട് ഡാറ്റാബേസിൽ ചേർക്കുന്നു."""
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO transactions (type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (type, amount, category, description, date))
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_summary_from_db():
    """ആകെ വരവ്, ചെലവ്, ബാക്കി തുക എന്നിവ നൽകുന്നു."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # ആകെ വരവ്
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Income'")
    income = cursor.fetchone()[0] or 0.0
    
    # ആകെ ചെലവ്
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Expense'")
    expense = cursor.fetchone()[0] or 0.0
    
    conn.close()
    return income, expense, income - expense

def get_all_transactions():
    """എല്ലാ ഇടപാടുകളും തിരികെ നൽകുന്നു."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, type, category, amount, description FROM transactions ORDER BY date DESC")
    transactions = cursor.fetchall()
    conn.close()
    return transactions

# --- 2. GUI Class (Tkinter കോഡ്) ---

class FinanceTrackerApp:
    def __init__(self, master):
        self.master = master
        master.title("💰 വരവ്-ചെലവ് ട്രാക്കർ (Finance Tracker)")
        master.geometry("850x650") # വിൻഡോയുടെ വലുപ്പം സജ്ജമാക്കുന്നു

        # ഡാറ്റാബേസ് സജ്ജീകരിക്കുന്നു
        initialize_db()

        # വേരിയബിളുകൾ
        self.amount_var = tk.DoubleVar()
        self.category_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.transaction_type = tk.StringVar(value="Income")

        # UI ഫ്രെയിമുകൾ
        self.create_input_frame(master)
        self.create_summary_frame(master)
        self.create_transaction_view_frame(master)

        # ഡാറ്റാബേസ് ഡാറ്റ ലോഡ് ചെയ്യുന്നു
        self.load_data()

    def create_input_frame(self, master):
        """ഇൻപുട്ട് നൽകാനുള്ള ഫ്രെയിം (വരവും ചെലവും ചേർക്കാൻ)"""
        input_frame = ttk.LabelFrame(master, text="പുതിയ ഇടപാട് ചേർക്കുക", padding="10")
        input_frame.pack(padx=10, pady=10, fill="x")

        # 1. ടൈപ്പ് (വരവോ ചെലവോ)
        ttk.Radiobutton(input_frame, text="Income (വരവ്)", variable=self.transaction_type, value="Income").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(input_frame, text="Expense (ചെലവ്)", variable=self.transaction_type, value="Expense").grid(row=0, column=1, padx=5, pady=5)

        # 2. തുക
        ttk.Label(input_frame, text="തുക:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.amount_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        # 3. വിഭാഗം (Category)
        ttk.Label(input_frame, text="വിഭാഗം:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.category_var, width=20).grid(row=2, column=1, padx=5, pady=5)

        # 4. വിവരണം (Description)
        ttk.Label(input_frame, text="വിവരണം:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.description_var, width=40).grid(row=3, column=1, columnspan=2, padx=5, pady=5)

        # 5. ബട്ടൺ
        ttk.Button(input_frame, text="ഇടപാട് ചേർക്കുക", command=self.add_transaction).grid(row=4, column=0, columnspan=3, pady=10)

    def create_summary_frame(self, master):
        """സാമ്പത്തിക സംഗ്രഹം പ്രദർശിപ്പിക്കാനുള്ള ഫ്രെയിം"""
        summary_frame = ttk.LabelFrame(master, text="സാമ്പത്തിക സംഗ്രഹം", padding="10")
        summary_frame.pack(padx=10, pady=5, fill="x")
        
        self.income_label = ttk.Label(summary_frame, text="ആകെ വരവ്: $0.00", font=('Arial', 12, 'bold'), foreground='green')
        self.income_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        self.expense_label = ttk.Label(summary_frame, text="ആകെ ചെലവ്: $0.00", font=('Arial', 12, 'bold'), foreground='red')
        self.expense_label.grid(row=0, column=1, padx=15, pady=5, sticky="w")
        
        self.balance_label = ttk.Label(summary_frame, text="നെറ്റ് ബാലൻസ്: $0.00", font=('Arial', 14, 'bold'))
        self.balance_label.grid(row=0, column=2, padx=15, pady=5, sticky="w")
        
    def create_transaction_view_frame(self, master):
        """എല്ലാ ഇടപാടുകളും കാണിക്കുന്ന പട്ടിക (Treeview)"""
        view_frame = ttk.LabelFrame(master, text="എല്ലാ ഇടപാടുകളും", padding="10")
        view_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("ID", "Date", "Type", "Category", "Amount", "Description")
        self.tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        # കോളങ്ങളുടെ തലക്കെട്ടുകൾ (Headings) സജ്ജമാക്കുന്നു
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W, width=100)
        
        self.tree.column("ID", width=30, anchor=tk.CENTER)
        self.tree.column("Date", width=120)
        self.tree.column("Amount", width=80, anchor=tk.E)
        self.tree.column("Description", width=200)

        # സ്ക്രോൾബാർ ചേർക്കുന്നു
        scrollbar = ttk.Scrollbar(view_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
    def add_transaction(self):
        """ഇൻപുട്ട് ഡാറ്റ പരിശോധിച്ച് ഡാറ്റാബേസിൽ ചേർക്കുന്നു."""
        try:
            amount = self.amount_var.get()
            category = self.category_var.get().strip()
            description = self.description_var.get().strip()
            type = self.transaction_type.get()
            
            if amount <= 0 or not category:
                messagebox.showerror("❌ പിശക്", "തുക പൂജ്യത്തേക്കാൾ കൂടുതലായിരിക്കണം, വിഭാഗം നിർബന്ധമാണ്.")
                return

            if add_transaction_to_db(type, amount, category, description):
                messagebox.showinfo("✅ വിജയം", f"{type} വിജയകരമായി ചേർത്തു.")
                # ഇൻപുട്ട് ബോക്സുകൾ ക്ലിയർ ചെയ്യുന്നു
                self.amount_var.set(0.0)
                self.category_var.set("")
                self.description_var.set("")
                # ഡാറ്റ വീണ്ടും ലോഡ് ചെയ്യുന്നു
                self.load_data()

        except ValueError:
            messagebox.showerror("❌ പിശക്", "തുക (Amount) ഒരു ശരിയായ സംഖ്യയായിരിക്കണം.")

    def load_data(self):
        """ഡാറ്റാബേസിൽ നിന്ന് സംഗ്രഹവും ഇടപാടുകളും ലോഡ് ചെയ്ത് GUI-യിൽ അപ്ഡേറ്റ് ചെയ്യുന്നു."""
        
        # സംഗ്രഹം അപ്ഡേറ്റ് ചെയ്യുക
        income, expense, balance = get_summary_from_db()
        self.income_label.config(text=f"ആകെ വരവ്: ${income:,.2f}")
        self.expense_label.config(text=f"ആകെ ചെലവ്: ${expense:,.2f}")
        self.balance_label.config(text=f"നെറ്റ് ബാലൻസ്: ${balance:,.2f}")
        
        # ഇടപാടുകൾ പട്ടികയിൽ അപ്ഡേറ്റ് ചെയ്യുക (Treeview)
        for item in self.tree.get_children():
            self.tree.delete(item) # പഴയ ഡാറ്റ നീക്കം ചെയ്യുന്നു
            
        transactions = get_all_transactions()
        
        for tx in transactions:
            # പട്ടികയിലേക്ക് പുതിയ ഡാറ്റ ചേർക്കുന്നു
            self.tree.insert('', tk.END, values=tx)


if __name__ == '__main__':
    root = tk.Tk()
    app = FinanceTrackerApp(root)
    root.mainloop()