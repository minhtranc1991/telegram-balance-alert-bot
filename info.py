import config
import json
from pathlib import Path
from datetime import datetime
import pytz
import time
from function import get_user_wallet_balance, send_message

def log_balance_history_to_json(balance, pnl, json_path="crypto_portfolio_optimization_balance_history_report.json"):
    # Tạo đường dẫn nếu chưa tồn tại
    path = Path(json_path)
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

def create_balance_message():
    initial_balance = 300

    try:
        balances = get_user_wallet_balance(config.acc_binance_1)
        if not balances:
            return "Error getting balance"

        # Tìm ví "Trading Bots"
        trading_bot_balance = next((float(b["balance"]) for b in balances if b["walletName"] == "Trading Bots"), 0)
        if trading_bot_balance is None:
            return "Error getting balance"
        else:
            accumulated_pnl = round((trading_bot_balance / initial_balance - 1) * 100, 2)

        # Ghi lại lịch sử vào file JSON
        log_balance_history_to_json(trading_bot_balance, accumulated_pnl)
        
        # Tạo message báo cáo
        message = "*Strategy:* Crypto Portfolio Optimization\n"
        message += "*Account:* teamhn48\n"
        message += f"*Equity (USDT):* {trading_bot_balance:.2f} USDT\n"
        message += f"*Time:* {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d')}\n"
        message += f"*Accumulated PnL (%):* {accumulated_pnl} %"

        return message
    except Exception as e:
        print(f"Error creating message: {e}")
        return "Error getting balance"

def send_balance_update():
    message = create_balance_message()
    send_message(message, config.token, config.channel_strat_id)

if __name__ == "__main__":
    while True:
        try:
            utc_now = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
            
            # Send update at 9:00 AM Vietnam time
            # if utc_now.hour == 9 and utc_now.minute == 0:
            send_balance_update()
            # print("Balance update sent")
            time.sleep(1)  # Sleep for 1 minute to avoid multiple sends
            # else:
                # time.sleep(1)  # Check every 30 seconds
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)