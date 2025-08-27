import json
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'Instantly.ai Analytics Report', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def create_pdf_report(json_file, pdf_file):
    # Read JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Initialize PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Get date range from first workspace
    first_workspace = next(iter(data['workspaces'].values()))
    dates = sorted(first_workspace['daily_totals'].keys())
    start_date = dates[0]
    end_date = dates[-1]
    
    # Title and Date Range
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f"Report Period: {start_date} to {end_date}", 0, 1, 'L')
    pdf.ln(5)
    
    # Overall Summary
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Overall Summary', 0, 1, 'L')
    pdf.set_font('Helvetica', '', 12)
    total_workspaces = len(data['workspaces'])
    total_sends = sum(workspace.get('total_sends', 0) for workspace in data['workspaces'].values())
    pdf.cell(0, 10, f"Total Workspaces: {total_workspaces}", 0, 1, 'L')
    pdf.cell(0, 10, f"Total Sends: {total_sends:,}", 0, 1, 'L')
    pdf.ln(5)
    
    # Per-Workspace Analysis
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Workspace Analysis', 0, 1, 'L')
    pdf.ln(5)
    
    for workspace_id, workspace_data in data['workspaces'].items():
        # Workspace Header
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, f"Workspace: {workspace_id}", 0, 1, 'L')
        pdf.set_font('Helvetica', '', 12)
        
        if workspace_data.get('error'):
            pdf.multi_cell(0, 10, f"Error: {str(workspace_data['error'])}", 0, 'L')
            pdf.cell(0, 10, f"Campaigns Processed: 0", 0, 1, 'L')
        else:
            pdf.cell(0, 10, f"Campaigns Processed: {workspace_data['campaigns_processed']}", 0, 1, 'L')
            pdf.cell(0, 10, f"Total Sends: {workspace_data['total_sends']:,}", 0, 1, 'L')
            
            # Daily Totals Table
            if workspace_data['daily_totals']:
                pdf.ln(5)
                pdf.set_font('Helvetica', 'B', 11)
                # Column headers
                col_width = pdf.get_string_width("2025-08-18") + 10
                pdf.cell(col_width, 10, 'Date', 1, 0, 'C')
                pdf.cell(col_width, 10, 'Sends', 1, 1, 'C')
                
                pdf.set_font('Helvetica', '', 11)
                for date, sends in sorted(workspace_data['daily_totals'].items()):
                    pdf.cell(col_width, 10, date, 1, 0, 'C')
                    pdf.cell(col_width, 10, f"{sends:,}", 1, 1, 'C')
        
        pdf.ln(10)
        
        # Add a new page if we're running out of space
        if pdf.get_y() > pdf.page_break_trigger:
            pdf.add_page()
    
    # Combined Daily Totals
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Combined Daily Totals (All Workspaces)', 0, 1, 'L')
    pdf.ln(5)
    
    # Calculate combined totals
    combined_totals = {}
    for workspace_data in data['workspaces'].values():
        if not workspace_data.get('error'):
            for date, sends in workspace_data['daily_totals'].items():
                combined_totals[date] = combined_totals.get(date, 0) + sends
    
    # Create table
    pdf.set_font('Helvetica', 'B', 11)
    col_width = pdf.get_string_width("2025-08-18") + 10
    pdf.cell(col_width, 10, 'Date', 1, 0, 'C')
    pdf.cell(col_width, 10, 'Total Sends', 1, 1, 'C')
    
    pdf.set_font('Helvetica', '', 11)
    for date, sends in sorted(combined_totals.items()):
        pdf.cell(col_width, 10, date, 1, 0, 'C')
        pdf.cell(col_width, 10, f"{sends:,}", 1, 1, 'C')
    
    # Generate timestamp
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 10)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pdf.cell(0, 10, f"Report generated on: {timestamp}", 0, 1, 'R')
    
    # Save the PDF
    pdf.output(pdf_file)

if __name__ == '__main__':
    json_file = 'daily_sends.json'
    pdf_file = 'analytics_report.pdf'
    
    try:
        create_pdf_report(json_file, pdf_file)
        print(f"\nPDF report successfully generated: {pdf_file}")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")