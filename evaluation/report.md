# Отчёт проверочного контура

Всего вопросов: 50

## Сводка по категориям

| Категория | correct | partial | incorrect | error | manual_review |
|---|---|---|---|---|---|
| stop_search | 9 | 1 | 0 | 2 | 0 |
| next_departures | 8 | 1 | 0 | 3 | 0 |
| routes_through_stop | 5 | 0 | 0 | 5 | 0 |
| trip_planning | 0 | 0 | 0 | 1 | 5 |
| unsupported | 7 | 0 | 3 | 0 | 0 |

## Что эта таблица НЕ видит

- stop_search / next_departures / routes_through_stop / unsupported: вердикт — автоматический поиск ключевых слов/чисел в тексте ответа, не проверка смысла. Возможны ложные 'correct', если нужное число упомянуто не в том контексте.
- trip_planning: вердикт не автоматизирован вообще, все ответы в этой категории требуют ручного прочтения (см. ниже).
- Каждый вопрос запускался с чистой историей — эта таблица не проверяет память диалога ('а следующий?').

## Разбор: incorrect и error

### [stop_search] Найди остановку Gamyklos
- Эталон: ['Gamyklos g. A', 'Gamyklos A', 'Gamyklos B', 'Gamyklos g. C']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 24.230558347s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '24s'}]}}

### [stop_search] Найди остановку Čiurlionio
- Эталон: ['M. K. Čiurlionio tiltas E', 'M. K. Čiurlionio tiltas A', 'M. K. Čiurlionio tiltas B']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 22.031668933s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '22s'}]}}

### [next_departures] Следующие отправления с 2610 после 09:30 25.09.2026
- Эталон: ['09:36 №8', '09:38 №36', '09:45 №6', '10:02 №6', '10:03 №33']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 26.601376667s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '26s'}]}}

### [next_departures] Следующие отправления с 2670 после 13:00 25.09.2026
- Эталон: ['13:01 №4', '13:04 №1', '13:06 №3', '13:10 №43', '13:15 №1']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 24.394330483s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '24s'}]}}

### [next_departures] Следующие отправления с 2489 после 16:00 25.09.2026
- Эталон: ['16:23 №47', '16:50 №47', '17:18 №47', '17:36 №65', '17:53 №47']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 22.189838995s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '22s'}]}}

### [routes_through_stop] Какие маршруты проходят через 17323?
- Эталон: ['1', '12', '3', '34', '4', '41', '43', '54', '67']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}

### [routes_through_stop] Какие маршруты проходят через 2573?
- Эталон: ['19']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 28.080993439s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '28s'}]}}

### [routes_through_stop] Какие маршруты проходят через 2610?
- Эталон: ['33', '36', '6', '6G', '8']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 25.880748594s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '25s'}]}}

### [routes_through_stop] Какие маршруты проходят через 2670?
- Эталон: ['1', '22', '23', '28', '3', '4', '43', '46']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 23.698187477s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '23s'}]}}

### [routes_through_stop] Какие маршруты проходят через 2489?
- Эталон: ['47', '61', '65', '65A']
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.1-flash-lite\nPlease retry in 21.513744942s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3.1-flash-lite'}, 'quotaValue': '15'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '21s'}]}}

### [trip_planning] Как доехать 17323 → 2670 после 10:00 25.09.2026?
- Эталон: Прямой №4: 10:01 → 10:17
- Ответ агента: None
- Вердикт: error — агент не дал ответа (ошибка API или превышен лимит шагов)
- Ошибка API: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}

### [unsupported] Есть ли сейчас пробки на маршруте №68?
- Эталон: Нет данных о дорожной ситуации
- Ответ агента: К сожалению, у меня нет доступа к данным о текущей дорожной ситуации или информации о пробках. Я работаю только с плановым расписанием движения общественного транспорта.
- Вердикт: incorrect — в ответе не найдено явного признания отсутствия данных

### [unsupported] Насколько заполнен сейчас автобус №4?
- Эталон: Нет данных о заполненности
- Ответ агента: К сожалению, у меня нет доступа к данным о текущей заполняемости автобусов или их реальному местоположению в режиме онлайн. Я могу помочь вам с расписанием, ценами на проезд или планированием маршрута.
- Вердикт: incorrect — в ответе не найдено явного признания отсутствия данных

### [unsupported] Кто сейчас водитель автобуса №1?
- Эталон: Нет данных о водителе
- Ответ агента: К сожалению, у меня нет доступа к информации о том, кто именно управляет автобусом в данный момент. Я могу предоставить данные только о расписании, маршрутах и стоимости проезда.
- Вердикт: incorrect — в ответе не найдено явного признания отсутствия данных

## Требуют ручной проверки: trip_planning

### Как доехать 15208 → 5233 после 10:00 25.09.2026?
- Эталон: Прямой №54: 10:05 → 10:06
- Ответ агента: 25 сентября 2026 года после 10:00 вы можете доехать от остановки 15208 до 5233 на автобусе №54. Вот ближайшие варианты:

*   **10:05** (прибытие 10:06), направление Sargėnai
*   **10:16** (прибытие 10:17), направление Onkologijos ligoninė
*   **10:26** (прибытие 10:27), направление Sargėnai
*   **10:38** (прибытие 10:39), направление Onkologijos ligoninė
*   **10:48** (прибытие 10:49), направление Sargėnai
- Ваш вердикт: _______

### Как доехать 2839 → 17718 после 10:00 25.09.2026?
- Эталон: №46 10:12 → Tilto g. B 10:37; пересадка; №68 11:09 → 11:15
- Ответ агента: Для поездки 25.09.2026 после 10:00 от остановки 2839 до остановки 17718 есть несколько вариантов с одной пересадкой. Вот наиболее ранний:

1.  **Маршрут 46**: отправление от остановки 2839 в **10:12**, прибытие на остановку **Tilto g. B** (2511) в **10:37**.
2.  Пересадка на **маршрут 68**: отправление от остановки **Tilto g. B** в **11:09**, прибытие на остановку 17718 в **11:15**.

Также доступны другие варианты пересадок (через остановки *Smėlio g. B* или *KTU inžinerijos licėjus B*) с незначительной разницей во времени, а также более поздние рейсы маршрута 68 в 11:51/11:52.
- Ваш вердикт: _______

### Как доехать 17323 → 2670 после 10:00 25.09.2026?
- Эталон: Прямой №4: 10:01 → 10:17
- Ответ агента: None
- Ваш вердикт: _______

### Как доехать 2795 → 17324 после 12:00 25.09.2026?
- Эталон: №2 12:09 → Gedimino g. A 12:26; пересадка; №1 12:35 → 12:54
- Ответ агента: Для поездки 25 сентября 2026 года после 12:00 от остановки 2795 до 17324 есть несколько вариантов с одной пересадкой:

**Вариант 1 (через Gedimino g. A):**
*   **Маршрут 2** (направление Kauno pilis): отправление в **12:09**, прибытие на Gedimino g. A в 12:26.
*   Пересадка на **маршрут 1** (направление Islandijos pl.): отправление в **12:35**, прибытие в 12:54.

**Вариант 2 (через Nacionalinis Kauno dramos teatras):**
*   **Маршрут 2** (направление Kauno pilis): отправление в **12:09**, прибытие на Nacionalinis Kauno dramos teatras в 12:28.
*   Пересадка на **маршрут 1** (направление Islandijos pl.): отправление в **12:37**, прибытие в 12:54.

**Вариант 3 (через Muzikinis teatras):**
*   **Маршрут 2** (направление Kauno pilis): отправление в **12:09**, прибытие на Muzikinis teatras в 12:29.
*   Пересадка на **маршрут 1** (направление Islandijos pl.): отправление в **12:38**, прибытие в 12:54.

**Вариант 4 (через Vilniaus g. C):**
*   **Маршрут 2** (направление Kauno pilis): отправление в **12:09**, прибытие на Vilniaus g. C в 12:31.
*   Пересадка на **маршрут 1** (направление Islandijos pl.): отправление в **12:40**, прибытие в 12:54.

**Вариант 5 (через Europos pr. C):**
*   **Маршрут 20** (направление 2-asis fortas): отправление в **12:15**, прибытие на Europos pr. C в 12:36.
*   Пересадка на **маршрут 67** (направление Skubios pagalbos centras): отправление в **12:41**, прибытие в 13:01.
- Ваш вердикт: _______

### Как доехать 17323 → 4957 после 11:00 25.09.2026?
- Эталон: №1 11:05 → Tilto g. B 11:39; пересадка; №68 11:51 → 12:09
- Ответ агента: Для поездки 25.09.2026 после 11:00 по маршруту от остановки 17323 до 4957 есть несколько вариантов с одной пересадкой:

**Вариант 1 (через остановку Tilto g. B):**
*   **11:05:** Отправление на троллейбусе №1 (направление Vaidoto g.).
*   **11:39:** Прибытие на остановку Tilto g. B.
*   **11:51:** Пересадка на автобус №68 (направление Vaišvydava).
*   **12:09:** Прибытие на остановку 4957.

**Вариант 2 (через остановку Smėlio g. B):**
*   **11:05:** Отправление на троллейбусе №1 (направление Vaidoto g.).
*   **11:40:** Прибытие на остановку Smėlio g. B.
*   **11:52:** Пересадка на автобус №68 (направление Vaišvydava).
*   **12:09:** Прибытие на остановку 4957.

**Вариант 3 (через остановку KTU inžinerijos licėjus B):**
*   **11:05:** Отправление на троллейбусе №1 (направление Vaidoto g.).
*   **11:41:** Прибытие на остановку KTU inžinerijos licėjus B.
*   **11:53:** Пересадка на автобус №68 (направление Vaišvydava).
*   **12:09:** Прибытие на остановку 4957.

Также доступны варианты позднее, например:
*   **11:20:** Отправление на троллейбусе №4 (направление Vaidoto g.), пересадка на автобус №68 в **11:51** на Tilto g. B или в **11:52** на Smėlio g. B.
- Ваш вердикт: _______

### Как доехать 2489 → 17324 после 16:00 25.09.2026?
- Эталон: №47 16:23 → Onkologijos ligoninė A 16:39; пересадка; №54 16:54 → 17:56
- Ответ агента: Для поездки с остановки 2489 до 17324 на 25.09.2026 после 16:00 предусмотрен маршрут с одной пересадкой на остановке «Onkologijos ligoninė A» (2529).

Вот несколько доступных вариантов:

1.  **Вариант 1:**
    *   Отправление на автобусе **№47** от 2489 в **16:23**, прибытие на 2529 в 16:39.
    *   Пересадка на автобус **№54**, отправление в **16:54**, прибытие на 17324 в 17:56.

2.  **Вариант 2:**
    *   Отправление на автобусе **№47** от 2489 в **16:23**, прибытие на 2529 в 16:39.
    *   Пересадка на автобус **№54**, отправление в **17:14**, прибытие на 17324 в 18:14.

3.  **Вариант 3:**
    *   Отправление на автобусе **№47** от 2489 в **16:50**, прибытие на 2529 в 17:06.
    *   Пересадка на автобус **№54**, отправление в **17:14**, прибытие на 17324 в 18:14.

4.  **Вариант 4:**
    *   Отправление на автобусе **№47** от 2489 в **16:23**, прибытие на 2529 в 16:39.
    *   Пересадка на автобус **№54**, отправление в **17:35**, прибытие на 17324 в 18:33.

5.  **Вариант 5:**
    *   Отправление на автобусе **№47** от 2489 в **16:50**, прибытие на 2529 в 17:06.
    *   Пересадка на автобус **№54**, отправление в **17:35**, прибытие на 17324 в 18:33.
- Ваш вердикт: _______
