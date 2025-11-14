"""
Module 3: Medicine Database & Inventory

This module manages the pharmacy's medicine inventory using SQLite.
It tracks medicine details, stock levels, and prescription frequencies.
"""

import sqlite3
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MedicineDatabase:
    """
    Manages the medicine inventory database for the pharmacy.
    
    This class provides methods to add, update, and query medicine information
    including stock levels and prescription frequencies.
    """
    
    def __init__(self, db_path: str = 'pharmacy.db'):
        """
        Initialize the Medicine Database.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        
        try:
            # Establish database connection
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"✓ Connected to database: {self.db_path}")
            
            # Create tables if they don't exist
            self._create_tables()
            
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _create_tables(self):
        """
        Create the medicines table if it doesn't already exist.
        
        Table schema:
            - id: INTEGER PRIMARY KEY (auto-increment)
            - name: TEXT UNIQUE (medicine name)
            - description: TEXT (medicine description/use)
            - stock_level: INTEGER (current stock quantity)
            - prescription_frequency: INTEGER (how many times prescribed, default 0)
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    stock_level INTEGER NOT NULL DEFAULT 0,
                    prescription_frequency INTEGER NOT NULL DEFAULT 0
                )
            ''')
            
            self.connection.commit()
            logger.info("✓ Medicines table ready")
            
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def add_medicine(self, name: str, description: str, stock_level: int) -> bool:
        """
        Add a new medicine to the database.
        
        Args:
            name (str): Name of the medicine (must be unique)
            description (str): Description or use of the medicine
            stock_level (int): Initial stock quantity
        
        Returns:
            bool: True if successful, False otherwise
        
        Raises:
            ValueError: If name is empty or stock_level is negative
        """
        # Input validation
        if not name or not name.strip():
            raise ValueError("Medicine name cannot be empty")
        
        if stock_level < 0:
            raise ValueError("Stock level cannot be negative")
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO medicines (name, description, stock_level, prescription_frequency)
                VALUES (?, ?, ?, 0)
            ''', (name.strip(), description.strip(), stock_level))
            
            self.connection.commit()
            logger.info(f"✓ Added medicine: {name} (Stock: {stock_level})")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Medicine '{name}' already exists in database")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding medicine: {e}")
            return False
    
    def update_stock(self, name: str, quantity_change: int) -> bool:
        """
        Update the stock level for a given medicine.
        
        Args:
            name (str): Name of the medicine
            quantity_change (int): Amount to add (positive) or remove (negative) from stock
        
        Returns:
            bool: True if successful, False otherwise
        
        Raises:
            ValueError: If the update would result in negative stock
        """
        try:
            cursor = self.connection.cursor()
            
            # First, get the current stock level
            cursor.execute('SELECT stock_level FROM medicines WHERE name = ?', (name,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Medicine '{name}' not found in database")
                return False
            
            current_stock = result[0]
            new_stock = current_stock + quantity_change
            
            # Validate that stock won't go negative
            if new_stock < 0:
                raise ValueError(f"Insufficient stock for '{name}'. Current: {current_stock}, Requested change: {quantity_change}")
            
            # Update the stock
            cursor.execute('''
                UPDATE medicines 
                SET stock_level = ?
                WHERE name = ?
            ''', (new_stock, name))
            
            self.connection.commit()
            
            change_type = "increased" if quantity_change > 0 else "decreased"
            logger.info(f"✓ Stock {change_type} for {name}: {current_stock} → {new_stock}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating stock: {e}")
            return False
    
    def increment_prescription_frequency(self, name: str) -> bool:
        """
        Increase the prescription frequency counter for a medicine by 1.
        
        This tracks how many times a medicine has been prescribed,
        useful for analytics and inventory management.
        
        Args:
            name (str): Name of the medicine
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE medicines 
                SET prescription_frequency = prescription_frequency + 1
                WHERE name = ?
            ''', (name,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Medicine '{name}' not found in database")
                return False
            
            self.connection.commit()
            logger.info(f"✓ Incremented prescription frequency for: {name}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error incrementing prescription frequency: {e}")
            return False
    
    def get_all_medicines(self) -> List[Dict]:
        """
        Retrieve all medicines from the database.
        
        Returns:
            List[Dict]: List of dictionaries, where each dictionary represents a medicine
                       with keys: id, name, description, stock_level, prescription_frequency
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('SELECT * FROM medicines ORDER BY name')
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            medicines = []
            for row in rows:
                medicines.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'stock_level': row['stock_level'],
                    'prescription_frequency': row['prescription_frequency']
                })
            
            logger.info(f"✓ Retrieved {len(medicines)} medicines from database")
            return medicines
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving medicines: {e}")
            return []
    
    def get_medicine_by_name(self, name: str) -> Optional[Dict]:
        """
        Retrieve a specific medicine by name.
        
        Args:
            name (str): Name of the medicine
        
        Returns:
            Dict or None: Dictionary with medicine details, or None if not found
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('SELECT * FROM medicines WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'stock_level': row['stock_level'],
                    'prescription_frequency': row['prescription_frequency']
                }
            else:
                logger.warning(f"Medicine '{name}' not found")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving medicine: {e}")
            return None
    
    def get_low_stock_medicines(self, threshold: int = 10) -> List[Dict]:
        """
        Get all medicines with stock level below a threshold.
        
        Args:
            threshold (int): Stock level threshold (default: 10)
        
        Returns:
            List[Dict]: List of medicines with low stock
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM medicines 
                WHERE stock_level < ?
                ORDER BY stock_level ASC
            ''', (threshold,))
            
            rows = cursor.fetchall()
            
            medicines = []
            for row in rows:
                medicines.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'stock_level': row['stock_level'],
                    'prescription_frequency': row['prescription_frequency']
                })
            
            if medicines:
                logger.warning(f"⚠️ {len(medicines)} medicines are low on stock (< {threshold})")
            
            return medicines
            
        except sqlite3.Error as e:
            logger.error(f"Error checking low stock: {e}")
            return []
    
    def close_connection(self):
        """
        Safely close the database connection.
        """
        if self.connection:
            self.connection.close()
            logger.info("✓ Database connection closed")


# Demo/Testing
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏥 MEDICINE DATABASE MODULE - DEMO")
    print("="*70 + "\n")
    
    # Initialize database
    db = MedicineDatabase('pharmacy.db')
    
    print("📋 Adding sample medicines...\n")
    
    # Add sample medicines
    sample_medicines = [
        {
            'name': 'Paracetamol',
            'description': 'Pain reliever and fever reducer',
            'stock_level': 150
        },
        {
            'name': 'Amoxicillin',
            'description': 'Antibiotic for bacterial infections',
            'stock_level': 75
        },
        {
            'name': 'Ibuprofen',
            'description': 'Anti-inflammatory pain reliever',
            'stock_level': 120
        },
        {
            'name': 'Metformin',
            'description': 'Medication for type 2 diabetes',
            'stock_level': 50
        },
        {
            'name': 'Lisinopril',
            'description': 'Medication for high blood pressure',
            'stock_level': 8
        }
    ]
    
    for med in sample_medicines:
        db.add_medicine(med['name'], med['description'], med['stock_level'])
    
    print("\n" + "="*70)
    print("📦 ALL MEDICINES IN INVENTORY")
    print("="*70 + "\n")
    
    # Get and display all medicines
    all_medicines = db.get_all_medicines()
    
    for med in all_medicines:
        print(f"ID: {med['id']}")
        print(f"Name: {med['name']}")
        print(f"Description: {med['description']}")
        print(f"Stock Level: {med['stock_level']}")
        print(f"Prescription Frequency: {med['prescription_frequency']}")
        print("-" * 70)
    
    print("\n" + "="*70)
    print("🔄 TESTING STOCK UPDATES")
    print("="*70 + "\n")
    
    # Test stock updates
    print("Prescribing 10 units of Paracetamol...")
    db.update_stock('Paracetamol', -10)
    db.increment_prescription_frequency('Paracetamol')
    
    print("\nRestocking 50 units of Amoxicillin...")
    db.update_stock('Amoxicillin', 50)
    
    print("\nPrescribing 5 units of Metformin...")
    db.update_stock('Metformin', -5)
    db.increment_prescription_frequency('Metformin')
    
    print("\n" + "="*70)
    print("⚠️ LOW STOCK ALERT (Threshold: 10)")
    print("="*70 + "\n")
    
    # Check for low stock
    low_stock = db.get_low_stock_medicines(10)
    
    if low_stock:
        for med in low_stock:
            print(f"⚠️ {med['name']}: Only {med['stock_level']} units remaining!")
    else:
        print("✓ All medicines are adequately stocked")
    
    print("\n" + "="*70)
    print("📊 UPDATED INVENTORY")
    print("="*70 + "\n")
    
    # Display updated inventory
    all_medicines = db.get_all_medicines()
    
    for med in all_medicines:
        stock_status = "⚠️ LOW" if med['stock_level'] < 10 else "✓"
        print(f"{stock_status} {med['name']}: Stock={med['stock_level']}, Prescribed={med['prescription_frequency']} times")
    
    # Close connection
    print("\n" + "="*70)
    db.close_connection()
    print("="*70)
    print("\n✅ Demo completed! Database saved to: pharmacy.db")
    print("You can inspect it using: sqlite3 pharmacy.db")
    print("="*70 + "\n")
