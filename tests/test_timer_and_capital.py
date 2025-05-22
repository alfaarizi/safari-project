import pytest
from my_safari_project.model.timer import Timer
from my_safari_project.model.capital import Capital

def test_timer_game_time_progression():
    timer = Timer()
    initial_time = timer.elapsed_seconds
    dt = timer.tick(1.0)
    assert timer.elapsed_seconds > initial_time
    assert dt > 0

def test_timer_date_format():
    timer = Timer()
    timer.elapsed_seconds = 50000
    date, time_str = timer.get_date_time()
    assert isinstance(date, str)
    assert isinstance(time_str, str)

def test_capital_fund_addition_and_deduction():
    capital = Capital(100)
    capital.addFunds(50)
    assert capital.getBalance() == 150

    success = capital.deductFunds(30)
    assert success
    assert capital.getBalance() == 120

    fail = capital.deductFunds(9999)
    assert not fail
    assert capital.getBalance() == 120

def test_bankruptcy_check():
    capital = Capital(10)
    capital.deductFunds(10)
    assert capital.checkBankruptcy() is True
