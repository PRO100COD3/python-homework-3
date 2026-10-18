import asyncio
import math
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()


class CalculateRequest(BaseModel):
    numbers: list[float]
    delays: list[float]


class CalculationResult(BaseModel):
    number: float
    square: float
    delay: float
    time: float


class CalculateResponse(BaseModel):
    results: list[CalculationResult]
    total_time: float
    parallel_faster_than_sequential: bool


async def calculate_square(number: float, delay: float):
    start_time = time.perf_counter()

    # Во время ожидания Python может выполнять другие задачи.
    await asyncio.sleep(delay)
    square = number * number

    elapsed_time = time.perf_counter() - start_time

    return CalculationResult(
        number=number,
        square=square,
        delay=delay,
        time=round(elapsed_time, 2),
    )


@app.post("/calculate/", response_model=CalculateResponse)
async def calculate(data: CalculateRequest):
    if len(data.numbers) != len(data.delays):
        raise HTTPException(
            status_code=400,
            detail="Количество чисел и задержек должно совпадать",
        )

    for delay in data.delays:
        if delay < 0 or not math.isfinite(delay):
            raise HTTPException(
                status_code=400,
                detail="Задержки должны быть конечными неотрицательными числами",
            )

    start_time = time.perf_counter()
    tasks = []

    for i in range(len(data.numbers)):
        tasks.append(calculate_square(data.numbers[i], data.delays[i]))

    # Запускаем задачи вместе. Результаты сохраняют порядок входных чисел.
    results = await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_time
    sequential_time = sum(data.delays)

    return CalculateResponse(
        results=results,
        total_time=round(total_time, 2),
        parallel_faster_than_sequential=total_time < sequential_time,
    )
