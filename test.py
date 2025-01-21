import camelot

# 提取表格
tables = camelot.read_pdf("提要分析.pdf", pages="all")

# 檢查表格
print(tables)

# 將表格保存為 Excel 或 CSV
tables[0].to_csv("table.csv")
tables[0].to_excel("table.xlsx")
