document_1 = """Item Category: Electronics
Item: Wireless Earbuds
Stock Level: 150
Online Orders: 45
Item Category: Electronics
Item: Smartwatch
Stock Level: 80
Online Orders: 22
Metadata:
Type: Report
Source: CAT - Comprehensive Assortment Tool
Context: Item level data and guides to aid in assortment decision making, including item ranks and add/delete/expansion recommendations.
Link: https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)
"""

# can you summarize the key insights from the weekly category performance report?
document_2 = """Category: Beverages
Customer KPIs: Customer Satisfaction: 92, Repeat Purchase Rate: 45, Average Basket Size: 18.50
Market Share: 15.3
Promotion Performance: Units Sold: 1200, Revenue Increase: 12.5
Category: Snacks
Customer KPIs: Customer Satisfaction: 88, Repeat Purchase Rate: 50, Average Basket Size: 22.30
Market Share: 12.8
Promotion Performance: Units Sold: 950, Revenue Increase: 9.8
Category: Household Essentials
Customer KPIs: Customer Satisfaction: 94, Repeat Purchase Rate: 60, Average Basket Size: 35.75
Market Share: 18.5
Promotion Performance: Units Sold: 1500, Revenue Increase: 15.2
Metadata:
Type: Report
Source: 84.51° Merch Insights Reporting
Context: Weekly category performance report highlighting Customer KPIs, Market Share, and Promotion Performance across key categories.
Link: https://en.wikipedia.org/wiki/Self-supervised_learning
"""

# show me the sales revenue for [specific item category] over the last 12 weeks.
document_3 = """Category: Beverages
Sales Revenue (Last 12 Weeks): [12000, 11500, 11800, 12200, 12500, 13000, 12800, 13200, 13500, 14000, 13800, 14200]
Category: Snacks
Sales Revenue (Last 12 Weeks): [9500, 9600, 9800, 10000, 10200, 10500, 10400, 10600, 10800, 11000, 11200, 11500]
Category: Household Essentials
Sales Revenue (Last 12 Weeks): [18000, 18500, 19000, 19500, 20000, 20500, 21000, 21500, 22000, 22500, 23000, 23500]
Metadata:
Type: Report
Source: POS Post Assortment Analysis Tracker - Summary File
Context: A high-level summary of sales revenue for total category and assortment classification over the last 12 weeks, based on POS PAAT data.
Link: https://en.wikipedia.org/wiki/Diffusion_model
"""

# where can I find web user behavior?
document_4 = """Category: Electronic
Behavioral Insights:
Top Attributes: Price Sensitivity, Brand Loyalty, Product Reviews
Shopping Patterns:
Frequency: High
Preferred Channels: Online, In-Store
Average Time Spent: 15 minutes
Web User Behavior:
Page Views: 12000
Add-to-Cart Rate: 8.5
Conversion Rate: 3.2
Category: Personal Care
Behavioral Insights:
Top Attributes: Ingredient Quality, Eco-Friendliness, Packaging
Shopping Patterns:
Frequency: Medium
Preferred Channels: Online
Average Time Spent: 10 minutes
Web User Behavior:
Page Views: 8500
Add-to-Cart Rate: 10.2
Conversion Rate: 4.5
Category: Home Decor
Behavioral Insights:
Top Attributes: Aesthetic Appeal, Durability, Price
Shopping Patterns:
Frequency: Low
Preferred Channels: Online
Average Time Spent: 20 minutes
Web User Behavior:
Page Views: 6000
Add-to-Cart Rate: 6.8
Conversion Rate: 2.7
Metadata:
Type: Application
Source: Merchandising Category Structures & Attributes
Context: Behavioral analysis of customer shopping patterns, including web user behavior, to identify how households shop a given category and the product attributes that motivate purchase decisions.
Link: https://en.wikipedia.org/wiki/Retrieval-augmented_generation
"""

# where can I find the recently added items ? 
document_5 = """Item Category: Beverages
New Items:
Item: Sparkling Water
Period: 1
Units Sold: 500
Revenue: 2500
Customer Feedback: 4.5
Item: Cold Brew Coffee
Period: 2
Units Sold: 450
Revenue: 2700
Customer Feedback: 4.7
Aggregated Metrics:
Total Units Sold: 950
Total Revenue: 5200
Average Customer Feedback: 4.6
Item Category: Household Essentials
New Items:
Item: Eco-Friendly Cleaner
Period: 1
Units Sold: 700
Revenue: 3500
Customer Feedback: 4.8
Item: Reusable Paper Towels
Period: 2
Units Sold: 650
Revenue: 3250
Customer Feedback: 4.7
Aggregated Metrics:
Total Units Sold: 1350
Total Revenue: 6750
Average Customer Feedback: 4.75
Metadata:
Type: Application
Source: New Item Tracker
Context: Sales performance summary of new items launched during KOMPASS events in the latest 13 periods, including multiple levels of aggregation for review.
Link: https://en.wikipedia.org/wiki/Fine-tuning_(deep_learning)
"""