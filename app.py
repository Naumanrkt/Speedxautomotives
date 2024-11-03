# app.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from dataclasses import dataclass
from typing import List, Dict
import plotly.express as px
import plotly.graph_objects as go

# Data Classes
@dataclass
class Part:
    id: str
    name: str
    price: float
    quantity: int
    reorder_level: int
    tax_rate: float = 0.1

@dataclass
class Service:
    id: str
    name: str
    base_price: float
    tax_rate: float = 0.1

@dataclass
class Customer:
    id: str
    name: str
    phone: str
    vehicle_number: str
    vehicle_model: str = ""
    email: str = ""

class AutoRepairShop:
    def __init__(self):
        self.parts = {}
        self.services = {}
        self.customers = {}
        self.invoices = []
        self.load_data()

    def load_data(self):
        """Load data from JSON files"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        files = {
            'parts.json': (self.parts, Part),
            'services.json': (self.services, Service),
            'customers.json': (self.customers, Customer),
            'invoices.json': self.invoices
        }
        
        for filename, (container, cls) in files.items():
            filepath = f"data/{filename}"
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if filename != 'invoices.json':
                        container.update({id: cls(**item) for id, item in data.items()})
                    else:
                        self.invoices = data
            except FileNotFoundError:
                if not self.parts and not self.services:
                    self.initialize_sample_data()

    def save_data(self):
        """Save data to JSON files"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        data_mapping = {
            'parts.json': {id: vars(part) for id, part in self.parts.items()},
            'services.json': {id: vars(service) for id, service in self.services.items()},
            'customers.json': {id: vars(customer) for id, customer in self.customers.items()},
            'invoices.json': self.invoices
        }
        
        for filename, data in data_mapping.items():
            with open(f'data/{filename}', 'w') as f:
                json.dump(data, f, indent=2)

    def initialize_sample_data(self):
        """Initialize sample data"""
        sample_parts = [
            Part("P001", "Oil Filter", 15.99, 50, 10),
            Part("P002", "Brake Pad", 45.99, 30, 8),
            Part("P003", "Engine Oil (1L)", 8.99, 100, 20)
        ]
        for part in sample_parts:
            self.parts[part.id] = part

        sample_services = [
            Service("S001", "Oil Change", 30.00),
            Service("S002", "Brake Service", 80.00),
            Service("S003", "General Inspection", 50.00)
        ]
        for service in sample_services:
            self.services[service.id] = service

# Initialize session state
if 'shop' not in st.session_state:
    st.session_state.shop = AutoRepairShop()

def save_data():
    st.session_state.shop.save_data()

# Streamlit UI
st.set_page_config(page_title="Auto Repair Shop Management", layout="wide")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", 
    ["Dashboard", "Inventory", "Services", "Customers", "Invoices", "Reports"])

# Dashboard
if page == "Dashboard":
    st.title("Auto Repair Shop Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quick Stats")
        st.write(f"Total Parts: {len(st.session_state.shop.parts)}")
        st.write(f"Total Services: {len(st.session_state.shop.services)}")
        st.write(f"Total Customers: {len(st.session_state.shop.customers)}")
        st.write(f"Total Invoices: {len(st.session_state.shop.invoices)}")

    with col2:
        st.subheader("Low Stock Alerts")
        low_stock = [part for part in st.session_state.shop.parts.values() 
                    if part.quantity <= part.reorder_level]
        if low_stock:
            for part in low_stock:
                st.warning(f"{part.name}: {part.quantity} remaining (Reorder at {part.reorder_level})")
        else:
            st.success("No items are low in stock")

# Inventory Management
elif page == "Inventory":
    st.title("Inventory Management")
    
    tab1, tab2 = st.tabs(["View Inventory", "Add New Part"])
    
    with tab1:
        if st.session_state.shop.parts:
            parts_df = pd.DataFrame([vars(part) for part in st.session_state.shop.parts.values()])
            st.dataframe(parts_df)
        else:
            st.info("No parts in inventory")
    
    with tab2:
        with st.form("add_part_form"):
            part_id = st.text_input("Part ID")
            name = st.text_input("Part Name")
            price = st.number_input("Price", min_value=0.0)
            quantity = st.number_input("Quantity", min_value=0)
            reorder_level = st.number_input("Reorder Level", min_value=0)
            tax_rate = st.number_input("Tax Rate", min_value=0.0, value=0.1)
            
            if st.form_submit_button("Add Part"):
                if part_id and name:
                    st.session_state.shop.parts[part_id] = Part(
                        part_id, name, price, quantity, reorder_level, tax_rate)
                    save_data()
                    st.success("Part added successfully!")
                else:
                    st.error("Please fill in all required fields")

# Services Management
elif page == "Services":
    st.title("Services Management")
    
    tab1, tab2 = st.tabs(["View Services", "Add New Service"])
    
    with tab1:
        if st.session_state.shop.services:
            services_df = pd.DataFrame([vars(service) for service in st.session_state.shop.services.values()])
            st.dataframe(services_df)
        else:
            st.info("No services available")
    
    with tab2:
        with st.form("add_service_form"):
            service_id = st.text_input("Service ID")
            name = st.text_input("Service Name")
            base_price = st.number_input("Base Price", min_value=0.0)
            tax_rate = st.number_input("Tax Rate", min_value=0.0, value=0.1)
            
            if st.form_submit_button("Add Service"):
                if service_id and name:
                    st.session_state.shop.services[service_id] = Service(
                        service_id, name, base_price, tax_rate)
                    save_data()
                    st.success("Service added successfully!")
                else:
                    st.error("Please fill in all required fields")

# Reports
elif page == "Reports":
    st.title("Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Sales Summary", "Popular Items", "Service Popularity"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")
    
    if st.button("Generate Report"):
        if report_type == "Sales Summary":
            # Calculate sales summary
            total_sales = sum(invoice["total"] for invoice in st.session_state.shop.invoices)
            total_tax = sum(invoice["tax"] for invoice in st.session_state.shop.invoices)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sales", f"${total_sales:.2f}")
            with col2:
                st.metric("Total Tax", f"${total_tax:.2f}")
            with col3:
                st.metric("Total Invoices", len(st.session_state.shop.invoices))
                
        elif report_type == "Popular Items":
            # Calculate popular items
            part_sales = {}
            for invoice in st.session_state.shop.invoices:
                for part in invoice["parts"]:
                    part_sales[part["name"]] = part_sales.get(part["name"], 0) + part["quantity"]
            
            if part_sales:
                fig = px.bar(
                    x=list(part_sales.keys()),
                    y=list(part_sales.values()),
                    title="Popular Items"
                )
                st.plotly_chart(fig)
            else:
                st.info("No sales data available")
                
        elif report_type == "Service Popularity":
            # Calculate service popularity
            service_count = {}
            for invoice in st.session_state.shop.invoices:
                for service in invoice["services"]:
                    service_count[service["name"]] = service_count.get(service["name"], 0) + 1
            
            if service_count:
                fig = px.pie(
                    values=list(service_count.values()),
                    names=list(service_count.keys()),
                    title="Service Popularity"
                )
                st.plotly_chart(fig)
            else:
                st.info("No service data available")

