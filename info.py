import function 
import config
import json
from datetime import datetime
from pathlib import Path
import pytz
import time
#DONT TRADE HERE
#DONT TRADE HERE
#DONT TRADE HERE
#DONT TRADE HERE


acc= config.acc_binance_1
symbol = 'BTCUSDT'
file_path = '/home/ubuntu/binance_MoFri/report.json'


        
def create_message(file_path,symbol): #update equity formula on March 9
    with open(file_path,'r') as f:
        data = json.load(f)
    current_price = float(function.check_price(symbol))
    positions = function.check_open_positions(acc,symbol)    
    position_info = positions[0]
    balance = function.check_balance_future(acc)
    unrealized_profit = round(float(position_info['unRealizedProfit']),2)
    amount = abs(float(position_info['positionAmt']))
    leverage = float(position_info['leverage'])
    current_position = len(positions)
    equity = round((amount * current_price)/leverage + balance ,2)
    
    initial_balance = 200
    accum_pnl = round((equity - initial_balance)/ initial_balance * 100,2)
    new_info = {
        'Date': datetime.now().strftime("%Y-%m-%d"),
        'Equity (USDT)': equity,
        'Accum_pnl': accum_pnl,
        'Current position': current_position
        
    }
 
    data.append(new_info)
    with open(file_path, 'w') as f:
        json.dump(data, f)

    message = (
            f"*Strategy:* Long Monday Short Friday\n"
            f"*Account:* Binance 1\n"
            f"*Equity (USDT):* {new_info['Equity (USDT)']} USDT\n"
            f"*Date:* {new_info['Date']}\n"
            f"*Accum Pnl(%):* {accum_pnl}%\n"
            f"*Current position:* {current_position}\n"
            f"*Unrealized PnL:* {unrealized_profit}\n"
        )
   
    return message

def log_balance_history_to_json(balance, pnl, json_path="crypto_portfolio_optimization_balance_history_report.json"):
    try:
        # Tạo đường dẫn nếu chưa tồn tại
        path = Path(json_path)
        print(path)
        if not path.exists():
            path.write_text("[]")  # Tạo file rỗng dạng list JSON nếu chưa có

        # Tải dữ liệu hiện có
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Tạo bản ghi mới
        record = {
            "Date": datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d"),
            "Equity (USDT)": round(balance, 2),
            "Accumulated PnL (%)": round(pnl, 2)
        }

        # Thêm vào danh sách và ghi lại
        data.append(record)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error logging balance history: {e}")

def portfolioopt_balance_message():
    initial_balance = 300

    try:
        balances = function.get_user_wallet_balance(config.acc_binance_2)
        if not balances:
            return "Error getting balance"

        # Tìm Trading Bots balance
        trading_bot_balance = next((float(b["balance"]) for b in balances if b["walletName"] == "Trading Bots"), None)
        if trading_bot_balance is None:
            return "Error getting Trading Bots balance"
        else:
            accumulated_pnl = round((trading_bot_balance / initial_balance - 1) * 100, 2)

        # Tìm Spot balance
        spot_balance = next((float(b["balance"]) for b in balances if b["walletName"] == "Spot"), None)
        if spot_balance is None:
            return "Error getting Spot balance"

        # Ghi lại lịch sử vào file JSON
        log_balance_history_to_json(trading_bot_balance, accumulated_pnl)

        # Tạo message báo cáo
        message =  f"----------------------------------------\n"
        message += f"*Strategy:* Crypto Portfolio Optimization\n"
        message += f"*Account:* teamhn48\n"
        message += f"*Equity (USDT):* {trading_bot_balance:.2f} USDT\n"
        message += f"*Date:* {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d')}\n"
        message += f"*Accumulated PnL (%):* {accumulated_pnl} %\n"
        message += f"----------------------------------------\n"
        message += f"*Spot Balance:* {spot_balance:.2f} USDT"

        return message

    except Exception as e:
        print(f"Error creating message: {e}")
        return "Error getting balance"

def update_telegram(file_path = file_path):
    message = create_message(file_path,symbol)
    message += portfolioopt_balance_message()
    function.send_message(message, config.token,config.channel_strat_id)

if __name__ == "__main__":
    while True:
        try:
            utc_now = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))

            if utc_now.hour == 8 and utc_now.minute == 59:
            # if True:
                with open ('report.json', 'r') as file:
                    data = json.load(file)
                    old_date = data[-1]['Date']
                    # print(f'Old date: {old_date}')

                current_date = utc_now.date().strftime("%Y-%m-%d")
                # print(f'Current date: {current_date}')
                if current_date != old_date:
                    update_telegram()
                    # print('hey')
            else:
                time.sleep(59)  # Sleep for 1 minute before checking again
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)
        



