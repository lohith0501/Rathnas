import streamlit as st
import pandas as pd
import warnings
from datetime import datetime
import plotly.express as px
from twilio.rest import Client

warnings.filterwarnings("ignore")

def main():

    #file load
    df_latest_stocks=pd.read_excel(".//Arcline_master_database.xlsx",
                               sheet_name="Latest_stocks")
    df_price_details=pd.read_excel(".//Arcline_master_database.xlsx",
                               sheet_name="Price_details")
    df_arcline_payment=pd.read_excel(".//Arcline_master_database.xlsx",
                               sheet_name="Arcline_payment")
    df_sales=pd.read_excel(".//Arcline_master_database.xlsx",
                               sheet_name="Sales")

    st.set_page_config(page_title='XYX', page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

    # Calculate days for invoice from invoice date
    df_sales['Invoice_date']=pd.to_datetime(df_sales['Invoice_date'], format='%Y-%m-%d')
    today = datetime.now()
    df_sales['DaysSincePurchase'] =(today - df_sales['Invoice_date']).dt.days

    #color settings 
    primary_color = "#34495e"  #  (a deep blue-gray)
    secondary_color = "#2c3e50"  # (a darker blue-gray)
    accent_color = "#e74c3c"  # (a shade of red for emphasis)
    background_color = "#ecf0f1"  # (a light gray)

    # sidebar title
    st.sidebar.markdown(f"<h1 style='color: {primary_color}; text-align: center;'>🚀 Distribution Unit</h1>", unsafe_allow_html=True)

    # sidebar subheading 
    st.sidebar.markdown(f"<div style='text-align: center;'><label style='color: {primary_color};'>Select your option</label></div>",
    unsafe_allow_html=True
    )
    selected_option = st.sidebar.selectbox("", ["Landing page","Arcline", "Payment notifications", "Weekly campaign"])

    # Landing page
    if selected_option=="Landing page":
         # title 
         title_style = f"color: {primary_color}; text-align: center;"
         st.markdown(f"<h1 style='{title_style}'>Rathnas Sales</h1>", unsafe_allow_html=True)
         st.image(".//landing_page.jpeg",  use_column_width=True)
         st.write("Welcome to Rathnas Sales Analytics, your premier destination for seamless insights into daily sales updates and business activities. Our user-friendly platform delivers real-time data, empowering you to effortlessly navigate intricate sales metrics and gain a nuanced understanding of your business performance. Beyond numerical analysis, Rathnas Sales Analytics is a strategic tool designed to enhance decision-making processes, ensuring that every click provides actionable intelligence for informed and precise business acumen.")

    # Arcline dashboard
    if selected_option=="Arcline":
         # title 
         title_style = f"color: {primary_color}; text-align: center;"
         st.markdown(f"<h1 style='{title_style}'>Arcline sales dashboard</h1>", unsafe_allow_html=True)
         
         
         # Centered radio buttons below the content using HTML and CSS
         st.markdown("""
                     <style>
                     .stRadio [role=radiogroup]{
                     align-items: center;
                     justify-content: center;
                     }
                     </style>
                     """,unsafe_allow_html=True)
         
         selected_radio_day_month_option = st.radio('', ["Overall", "Monthly"], index=0,horizontal=True)
         
         if selected_radio_day_month_option == 'Overall':
             # Total invoice amount
             total_invoice_amount=(
                 df_sales
                 .Invoice_amount
                 .sum()
                )
             
             total_credit_amount=(
                 df_sales
                 .Credit_note
                 .sum()
                )
             
             total_received_amount=(
                 df_sales
                 .Amount_received
                 .sum()
                )
             
             total_amount_paid_to_arcline=int(
                 df_arcline_payment
                 .query("Status=='PAID'")
                 .Amount
                 .sum()
                 )
             
             Total_stock_amount=int(
                 pd.merge(
                     (
                         df_latest_stocks
                         .assign(category_model=lambda x:x.Category+x.Model)
                         .loc[:,["category_model","Quantity"]]
                     ),
                     (
                         df_price_details
                         .assign(category_model=lambda x:x.Category+x.Model)
                         .loc[:,["category_model","Incoming_price"]]
                         ),
                         on="category_model",
                         how="left"
                         )
                         .assign(Price=lambda x:x.Quantity*x.Incoming_price)
                         .Price
                         .sum()
                         )
             
             df_outstanding=(
                 pd.merge(
                     (
                          df_sales
                          .loc[:,["Customer_name","Location","Invoice_amount"]]
                          .groupby(["Customer_name","Location"])["Invoice_amount"]
                          .sum()
                          .reset_index()
                          .assign(customer_location=lambda x:x.Customer_name+x.Location)
                     ),
                     (
                          df_sales
                          .assign(customer_location=lambda x:x.Customer_name+x.Location)
                          .loc[:,["customer_location","Amount_received","Credit_note","Discount"]]
                          .groupby(["customer_location"])[["Amount_received","Credit_note","Discount"]]
                          .sum()
                          .reset_index()
                    ),
                    on="customer_location",
                    how="left"
                          )
                .assign(Adjusted_Invoice_amount=lambda x:(x.Invoice_amount-x.Credit_note)-(x.Discount))
                .assign(Outstanding=lambda x:x.Adjusted_Invoice_amount-x.Amount_received)
                .loc[:,["Customer_name","Location","Invoice_amount","Amount_received","Credit_note","Outstanding"]]
            )
             
             total_outstanding=(
                 df_outstanding
                 .Outstanding
                 .sum()
                 )
             
             Amount_overdue= (
                 df_sales
                 .assign(Payments_delta=lambda x:(x.Invoice_amount-x.Credit_note)-(x.Amount_received+x.Discount))
                 .query("Payments_delta>0")
                 .query("DaysSincePurchase>45")
                 .sort_values("DaysSincePurchase",ascending=False)
                 .Invoice_amount
                 .sum()
             )

             Dealer_count_overdue=(
                 df_sales
                 .assign(Payments_delta=lambda x:(x.Invoice_amount-x.Credit_note)-(x.Amount_received+x.Discount))
                 .query("Payments_delta>0")
                 .query("DaysSincePurchase>45")
                 .sort_values("DaysSincePurchase",ascending=False)
                 .Customer_name
                 .nunique()
                 )
             
             Dealers_with_no_committed_date=(
                 df_sales
                 .assign(Payments_delta=lambda x:(x.Invoice_amount-x.Credit_note)-(x.Amount_received+x.Discount))
                 .query("Payments_delta>0")
                 .query("DaysSincePurchase>45")
                 .sort_values("DaysSincePurchase",ascending=False)
                 .Committed_date
                 .isna()
                 .sum()
             )

             df_Overdue_based_on_ageing=(
                 df_sales
                 .assign(Payments_delta=lambda x:(x.Invoice_amount-x.Credit_note)-(x.Amount_received+x.Discount))
                 .query("Payments_delta>0")
                 .query("DaysSincePurchase>45")
                 .sort_values("DaysSincePurchase",ascending=False)
                 .drop(["Payments_delta"],axis=1)
                 .reset_index(drop=True)
             )

             # Row A
             a1, a2, a3 = st.columns(3)
             a1.metric("Total Invoice raised", total_invoice_amount)
             a2.metric("Credit Note",total_credit_amount)
             a3.metric("Amount Received", total_received_amount)

             # Row B
             b1, b2, b3 = st.columns(3) 
             b1.metric("Amount paid to Arcline", total_amount_paid_to_arcline)
             b2.metric("Total stock",Total_stock_amount)
             b3.metric("Outstanding", total_outstanding) 

             # Row C
             c1, c2, c3 = st.columns(3) 
             c1.metric("Overdue amount", Amount_overdue)
             c2.metric("Overdue Dealers count ",Dealer_count_overdue)
             c3.metric("No committed dates dealer count", Dealers_with_no_committed_date)   

             Overdue_dealers_for_plot=(
                 df_sales
                 .assign(Payments_delta=lambda x:(x.Invoice_amount-x.Credit_note-x.Discount)-(x.Amount_received))
                 .query("Payments_delta>0")
                 .query("DaysSincePurchase>45")
                 .sort_values("DaysSincePurchase",ascending=False)
                 .drop(["Payments_delta"],axis=1)
                 .reset_index(drop=True)
                 .loc[:,["Customer_name","DaysSincePurchase"]]
                                       )
             
             Overdue_dealers_for_plot=Overdue_dealers_for_plot.sort_values(by='DaysSincePurchase', ascending=False)


             # Create a horizontal bar chart with Plotly Express
             fig_overdue_dealers = px.bar(Overdue_dealers_for_plot, x='DaysSincePurchase', y='Customer_name', orientation='h',
             category_orders={'Customer_name': Overdue_dealers_for_plot['Customer_name'].unique()},
             labels={'DaysSincePurchase': 'DaysSincePurchase', 'Invoice_number': 'Invoice_number',
                     'Invoice_date':'Invoice_date','Invoice_amount':'Invoice_amount'}
                     )
             
             fig_overdue_dealers.update_layout(
                 title='<b>Overdue dealers (Number of days ageing)</b>',
                 title_x=0.5,
                 title_y=0.95,
                 title_pad=dict(t=10),
                 xaxis_title='Days from date of purchase',
                 yaxis_title='Dealer name',
                 width=1000
                  )
             
             # Set chart layout for a cleaner look
             fig_overdue_dealers.update_layout(
                 paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                 plot_bgcolor='rgba(0,0,0,0)'    # Transparent plot area
                              )

             # Display the chart using Streamlit
             st.plotly_chart(fig_overdue_dealers )   

             df_overdue_dealers=(
                 df_sales
                 .assign(Payments_delta=lambda x:(x.Invoice_amount-x.Credit_note-x.Discount)-(x.Amount_received))
                 .query("Payments_delta>0")
                 .query("DaysSincePurchase>45")
                 .sort_values("DaysSincePurchase",ascending=False)
                 .drop(["Payments_delta"],axis=1)
                 .reset_index(drop=True)
                                       )
             
             st.dataframe(df_overdue_dealers)

             
         elif selected_radio_day_month_option == 'Monthly':
             st.write("You selected Monthly. Add your code for this option.")
    
    if selected_option=="Payment notifications":
        TWILIO_ACCOUNT_SID = "AC5ce82ec4312733d6cf6aa2bc6e72610c"
        TWILIO_AUTH_TOKEN = "cc7446cbdd0beebfff5d71e5cb204604"
        TWILIO_PHONE_NUMBER = "+918095838485"
        TWILIO_WHATSAPP_NUMBER = "+14155238886"  # Twilio's WhatsApp Sandbox number

        # Create Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        st.title("WhatsApp Message Sender")

        name = st.text_input("Enter your name:")
        phone_number = st.text_input("Enter your phone number (include country code, e.g., +123456789):")
        message_body = st.text_area("Type your message:", "Thank you for providing payment!")

        # Button to send WhatsApp message
        if st.button("Send WhatsApp Message"):
            if name and phone_number and message_body:
                composed_message = f"Hello {name}, {message_body}"
                try:
                    message = client.messages.create(
                    body=composed_message,
                    from_=TWILIO_WHATSAPP_NUMBER,
                    to=f"whatsapp:{phone_number}"
                    )
                    st.success(f"WhatsApp message sent successfully to {phone_number}!")
                except Exception as e:
                    st.error(f"Error sending WhatsApp message: {e}")
                else:
                    st.warning("Please enter your name and phone number before sending the message.")
    



if __name__=="__main__":
    main()



