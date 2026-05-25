# Диаграммы для ВКР: AnimeAttire

Актуализировано по текущему состоянию репозитория на основе:
- `ORCHESTRATION_PLAN.txt`
- `backend/users/views.py`
- `backend/catalog/views.py`
- `backend/catalog/services.py`
- `backend/catalog/serializers.py`
- `frontend/components/account/account-page.tsx`
- `frontend/components/product/product-detail-page.tsx`

Проект сейчас корректно позиционировать не просто как интернет-магазин одежды, а как **интеллектуальный онлайн-магазин одежды с умной примерочной, подбором размера, капсульными образами и снижением риска возвратов**.

Ниже — актуальный список диаграмм для диплома: что уже реально есть в системе, что стоит показывать на схемах и какие акценты делать на защите.

## 1. Что обязательно поменялось

По сравнению с базовой версией магазина, в диаграммах теперь обязательно должны отражаться:

- `fit-profile` пользователя: рост, вес, мерки, предпочтительная посадка, стиль, сезон, размеры верха/низа, бюджет, заметки;
- персональная рекомендация по размеру;
- текстовое объяснение, почему выбран именно этот размер;
- предупреждения: низкая точность, стиль/сезон не совпадает, выбран ближайший размер, нужен более полный профиль;
- капсульный образ из нескольких вещей;
- отдельный API и UI-поток для умной примерочной;
- различие между уже реализованным функционалом и тем, что пока запланировано.

## 2. Что уже реализовано и можно честно показывать

### Уже есть в коде

- профиль пользователя и редактирование fit-profile:
  - `backend/users/views.py:107`
  - `frontend/components/account/account-page.tsx:581`
- рекомендательная логика на backend:
  - `backend/catalog/services.py:292`
- рекомендация в детальной карточке товара:
  - `backend/catalog/serializers.py:109`
  - `frontend/components/product/product-detail-page.tsx:324`
- отдельная recommendation endpoint:
  - `backend/catalog/views.py:108`
- капсульные образы в рекомендации:
  - `backend/catalog/services.py:219`
  - `frontend/components/product/product-detail-page.tsx:399`

### Ещё не реализовано полностью

- отдельный wizard smart fitting вне личного кабинета;
- рекомендации на странице каталога;
- история/сохранение рекомендаций;
- админские инструменты для настройки правил рекомендаций;
- полноценная recommendation-аналитика для поддержки и качества модели.

Поэтому в ВКР лучше формулировать это так:
- **реализовано:** умная примерочная v1, fit-profile, рекомендации в карточке товара, капсульный образ;
- **в перспективе / следующем этапе:** рекомендации в каталоге, recommendation history, расширенные админские инструменты.

## 3. Обязательный набор диаграмм

Если нужен минимальный, но сильный комплект для диплома:

- Use Case Diagram
- User Flow / Customer Journey
- BPMN процесса покупки
- ERD
- Sequence Diagram для smart fitting
- Sequence Diagram для checkout
- Component Diagram
- Deployment Diagram
- State Machine Diagram для заказа

## 4. Use Case Diagram

**Цель:** показать, кто и какие функции системы использует.

### Акторы

- Гость
- Покупатель
- Администратор / контент-менеджер
- Менеджер заказов
- Платёжный провайдер
- Служба доставки

### Обязательные use cases

- Просмотр каталога
- Поиск, фильтрация, сортировка
- Просмотр карточки товара
- Регистрация / вход / выход
- Работа с корзиной
- Оформление заказа
- Оплата заказа
- Просмотр истории заказов
- Работа с избранным
- Обращение в поддержку
- Управление профилем и адресами
- **Заполнение fit-profile**
- **Получение рекомендации по размеру**
- **Получение капсульного образа**
- CRUD товаров, категорий, франшиз, вариантов, изображений
- Управление заказами и статусами

### Важные include / extend

- `Просмотр карточки товара` -> `Получение рекомендации по размеру`
- `Получение рекомендации по размеру` -> `Анализ fit-profile`
- `Получение рекомендации по размеру` -> `Показ объяснения выбора`
- `Получение рекомендации по размеру` -> `Показ предупреждений`
- `Просмотр карточки товара` -> `Получение капсульного образа`

## 5. User Flow / Customer Journey

**Цель:** показать пользовательский путь без перегруза техническими деталями.

### Актуальный главный сценарий

1. Пользователь открывает сайт
2. Переходит в каталог
3. Открывает карточку товара
4. Видит рекомендацию по размеру
5. При необходимости идёт в аккаунт и заполняет fit-profile
6. Возвращается к товару
7. Получает более точную рекомендацию и капсульный образ
8. Добавляет товар в корзину
9. Оформляет заказ
10. Оплачивает заказ
11. Отслеживает заказ в личном кабинете

### Отдельный flow для smart fitting

1. Вход в аккаунт
2. Открытие раздела профиля
3. Заполнение параметров фигуры и предпочтений
4. Сохранение fit-profile
5. Повторный просмотр карточки товара
6. Получение персональной рекомендации
7. Принятие решения о покупке

## 6. BPMN 2.0: бизнес-процесс покупки

**Цель:** формально показать путь заказа от создания до завершения.

### Дорожки

- Покупатель
- Frontend / система
- Backend API
- Платёжный провайдер
- Склад / менеджер заказов
- Служба доставки

### Основная логика

- Выбор товара
- Проверка доступности варианта
- Получение рекомендации по размеру
- Добавление в корзину
- Создание заказа
- Создание платёжной сессии
- Подтверждение оплаты
- Комплектация
- Передача в доставку
- Отслеживание
- Доставка
- Завершение / возврат / отмена

### Что важно показать отдельно

- если fit-profile неполный -> рекомендация даётся с низкой точностью;
- если точного размера нет -> выбирается ближайший;
- если стиль/сезон не совпадает -> показывается предупреждение;
- если оплата не прошла -> возврат в сценарий оплаты.

## 7. DFD

**Цель:** показать потоки данных.

### Context Diagram (Level 0)

Один процесс: `Система AnimeAttire`

Внешние сущности:
- Покупатель
- Администратор
- Платёжный провайдер
- Служба доставки

Потоки:
- запросы каталога;
- данные профиля и fit-profile;
- данные корзины и заказа;
- платёжные данные;
- статусы доставки;
- рекомендации по размеру и образу.

### Level 1

Разбить минимум на процессы:

- Управление аккаунтом
- Управление fit-profile
- Каталог и карточка товара
- Recommendation engine
- Корзина
- Checkout / Orders
- Payments
- Delivery tracking
- Admin catalog management

## 8. ERD

**Цель:** показать модель данных.

### Сущности, которые обязательно должны быть на диаграмме

- `User`
- `Address`
- `Category`
- `AnimeFranchise`
- `Product`
- `ProductVariant`
- `ProductImage`
- `ProductTag`
- `ProductRelation`
- `Cart`
- `CartItem`
- `Order`
- `OrderItem`
- `DeliveryMethod`
- `OrderDeliverySnapshot`
- `DeliveryTrackingEvent`
- `PaymentMethod`
- `Payment`
- `PaymentEvent`
- `PaymentRefund`
- `FavoriteProduct`
- `ContactRequest`

### Отдельный акцент для диплома

Так как отдельной таблицы `FitProfile` нет, нужно честно показать, что:

- `fit_profile` хранится в `User` как структурированное JSON-поле;
- `fit_profile_updated_at` хранится в `User`;
- recommendation v1 вычисляется сервисным слоем, а не отдельной таблицей рекомендаций.

Это хороший аргумент на защите: решение минимизирует сложность модели данных на MVP-этапе.

## 9. Sequence Diagram: smart fitting

**Это теперь одна из ключевых диаграмм диплома.**

### Сценарий 1: заполнение fit-profile

Участники:
- Покупатель
- Account UI
- API
- User service / serializer
- DB

Поток:
1. Пользователь открывает аккаунт
2. Frontend запрашивает текущий `fit-profile`
3. API возвращает данные
4. Пользователь редактирует параметры
5. Frontend отправляет `PATCH /users/me/fit-profile/`
6. Backend валидирует данные
7. Данные сохраняются в `User.fit_profile`
8. API возвращает обновлённый профиль
9. UI обновляет состояние

### Сценарий 2: рекомендация на карточке товара

Участники:
- Покупатель
- Product page
- Product API
- Recommendation service
- DB

Поток:
1. Пользователь открывает карточку товара
2. Frontend запрашивает товар
3. Backend сериализует товар
4. Serializer вызывает recommendation service
5. Сервис анализирует:
   - fit-profile пользователя;
   - доступные размеры;
   - посадку товара;
   - стиль и сезон;
   - связанные товары
6. Возвращается:
   - recommended size;
   - confidence;
   - summary;
   - explanation;
   - warnings;
   - outfit
7. Frontend показывает рекомендацию

## 10. Sequence Diagram: checkout

**Цель:** показать связку frontend, orders, payments и delivery.

Участники:
- Покупатель
- Checkout UI
- Orders API
- Payments API / provider
- Delivery service

Основной поток:
1. Пользователь отправляет checkout
2. Backend создаёт заказ
3. Создаётся платёжная сессия
4. Пользователь оплачивает
5. Платёжный провайдер присылает webhook
6. Backend обновляет статус заказа
7. Заказ уходит в комплектацию
8. Создаётся доставка / трекинг

## 11. Component Diagram

**Цель:** показать основные подсистемы.

### Актуальные компоненты

- `Next.js Frontend`
  - Home / Catalog UI
  - Product Detail UI
  - Cart / Checkout UI
  - Account UI
  - Smart Fitting UI
- `Django + DRF Backend`
  - Auth / Users
  - Catalog
  - Recommendation Service
  - Cart
  - Orders
  - Payments
  - Delivery
  - Support
  - Favorites
- `PostgreSQL`
- `Redis / background processing` — если показываешь как инфраструктурную часть
- `Object Storage / media`
- `Payment Provider`
- `Delivery Provider`

### Что важно выделить

- recommendation engine сейчас является частью backend service layer;
- fit-profile приходит из пользовательского модуля;
- recommendation block встраивается в product detail serializer;
- капсульный образ строится на основе `ProductRelation` и каталога.

## 12. Deployment Diagram

**Цель:** показать развёртывание системы.

### Узлы

- Browser
- Frontend server / Next.js
- Backend server / Django API
- PostgreSQL
- Media storage
- Payment provider
- Delivery provider

Если хочешь показать локальную/dev-схему, можно отдельно сделать упрощённый вариант:
- Browser
- Frontend `127.0.0.1:3000`
- Backend API
- PostgreSQL

## 13. State Machine Diagram: заказ

**Цель:** формально показать жизненный цикл заказа.

Актуальные состояния лучше брать из кода:

- `pending`
- `paid`
- `picking`
- `packed`
- `shipped`
- `delivered`
- `cancelled`
- `returned`

Переходы:
- `pending -> paid`
- `paid -> picking`
- `picking -> packed`
- `packed -> shipped`
- `shipped -> delivered`
- возможны переходы в `cancelled`
- после завершения сценария возврата возможен `returned`

## 14. Activity Diagram: алгоритм рекомендации размера

**Это новая важная диаграмма, её очень желательно добавить в диплом.**

### Что показать

1. Получить товар и пользователя
2. Проверить, авторизован ли пользователь
3. Проверить, заполнен ли fit-profile
4. Получить активные варианты размеров
5. Определить, нужен верхний или нижний размер
6. Учесть:
   - обычный размер пользователя;
   - мерки;
   - рост и вес;
   - preferred fit;
   - fit товара;
7. Найти ближайший доступный размер
8. Сформировать confidence
9. Сформировать warnings
10. Сформировать explanation
11. Подобрать капсульный образ
12. Вернуть recommendation response

### Ветвления

- профиль пустой -> low/no confidence;
- нет активных размеров -> рекомендация недоступна;
- точного размера нет -> выбрать ближайший;
- стиль/сезон не совпадает -> warning.

## 15. Activity Diagram: подбор капсульного образа

Тоже полезно добавить отдельно, если нужно усилить новизну проекта.

### Логика

1. Взять основной товар
2. Проверить связанные товары `ProductRelation`
3. Если связей нет — взять fallback по франшизе / каталогу
4. Отфильтровать дубли категорий
5. Проверить стиль
6. Проверить бюджет
7. Собрать 2–3 совместимых позиции
8. Посчитать итоговую сумму
9. Вернуть набор вещей и причины выбора

## 16. Sitemap / структура экранов

Можно добавить как вспомогательную диаграмму.

### Актуальные страницы

- Главная
- Каталог
- Карточка товара
- Корзина
- Checkout
- Личный кабинет
- Заказы
- Избранное
- Контакты
- Страницы доставки / возврата / политики

### Для smart fitting важно отразить

- `Аккаунт -> Fit-profile`
- `Карточка товара -> Recommendation block`
- в будущем:
  - `Каталог -> Capsule recommendations`
  - `Wizard smart fitting`

## 17. Что лучше всего показывать на защите

Если времени мало, акцентируйся на 5 диаграммах:

- Use Case
- ERD
- Sequence Diagram: smart fitting
- Activity Diagram: recommendation engine
- Component Diagram

Именно они лучше всего доказывают, что проект отличается от обычного интернет-магазина.

## 18. Короткий вывод для текста ВКР

Можно использовать такую формулировку:

> Оригинальность проектируемой системы заключается в интеграции механизма умной примерочной в структуру интернет-магазина. В отличие от классических e-commerce решений, где пользователь самостоятельно выбирает размер и сочетаемость вещей, система AnimeAttire анализирует параметры пользователя, предпочтения по стилю и посадке, после чего формирует рекомендацию по размеру, предупреждения о возможных рисках и готовый капсульный образ. Это позволяет снизить неопределённость при покупке одежды онлайн и уменьшить вероятность возвратов.

## 19. PlantUML-код для каждой диаграммы

Ниже — готовые шаблоны `PlantUML`, которые можно использовать как основу для вставки в диплом, `PlantUML Server`, `draw.io` c плагином или локальный рендерер.

Для `BPMN`, `DFD`, `User Flow` и `Sitemap` используется не строго нативная нотация BPMN/DFD, а максимально близкое представление средствами `PlantUML`, чего обычно достаточно для ВКР.

### 19.1. Use Case Diagram

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle

actor "Гость" as Guest
actor "Покупатель" as Customer
actor "Администратор /\nконтент-менеджер" as Admin
actor "Менеджер заказов" as OrderManager
actor "Платёжный провайдер" as PaymentProvider
actor "Служба доставки" as DeliveryService

rectangle "AnimeAttire" {
  usecase "Просмотр каталога" as UC_Catalog
  usecase "Поиск, фильтрация,\nсортировка" as UC_Search
  usecase "Просмотр карточки товара" as UC_Product
  usecase "Регистрация / вход / выход" as UC_Auth
  usecase "Работа с корзиной" as UC_Cart
  usecase "Оформление заказа" as UC_Checkout
  usecase "Оплата заказа" as UC_Payment
  usecase "История заказов" as UC_Orders
  usecase "Избранное" as UC_Favorites
  usecase "Обращение в поддержку" as UC_Support
  usecase "Управление профилем\nи адресами" as UC_Profile
  usecase "Заполнение fit-profile" as UC_FitProfile
  usecase "Получение рекомендации\nпо размеру" as UC_SizeRecommendation
  usecase "Анализ fit-profile" as UC_FitAnalysis
  usecase "Показ объяснения выбора" as UC_Explanation
  usecase "Показ предупреждений" as UC_Warnings
  usecase "Получение капсульного\nобраза" as UC_Capsule
  usecase "CRUD товаров, категорий,\nфраншиз, вариантов, изображений" as UC_AdminCatalog
  usecase "Управление заказами\nи статусами" as UC_AdminOrders
}

Guest --> UC_Catalog
Guest --> UC_Search
Guest --> UC_Product
Guest --> UC_Auth

Customer --> UC_Catalog
Customer --> UC_Search
Customer --> UC_Product
Customer --> UC_Cart
Customer --> UC_Checkout
Customer --> UC_Payment
Customer --> UC_Orders
Customer --> UC_Favorites
Customer --> UC_Support
Customer --> UC_Profile
Customer --> UC_FitProfile
Customer --> UC_SizeRecommendation
Customer --> UC_Capsule

Admin --> UC_AdminCatalog
OrderManager --> UC_AdminOrders
PaymentProvider --> UC_Payment
DeliveryService --> UC_AdminOrders

UC_Product .> UC_SizeRecommendation : <<include>>
UC_SizeRecommendation .> UC_FitAnalysis : <<include>>
UC_SizeRecommendation .> UC_Explanation : <<include>>
UC_SizeRecommendation .> UC_Warnings : <<include>>
UC_Product .> UC_Capsule : <<include>>
UC_Checkout .> UC_Payment : <<include>>
@enduml
```

### 19.2. User Flow / Customer Journey

```plantuml
@startuml
start
:Открыть сайт AnimeAttire;
:Перейти в каталог;
:Выбрать товар;
:Открыть карточку товара;

if (Есть fit-profile?) then (да)
  :Показать персональную\nрекомендацию по размеру;
else (нет)
  :Показать базовую рекомендацию\nс низкой точностью;
  :Перейти в аккаунт;
  :Заполнить fit-profile;
  :Сохранить параметры;
  :Вернуться к товару;
  :Показать точную рекомендацию;
endif

:Показать warnings,\nexplanation и capsule outfit;

if (Товар подходит?) then (да)
  :Добавить в корзину;
  :Перейти к checkout;
  :Заполнить данные заказа;
  :Оплатить заказ;
  :Получить подтверждение;
  :Отслеживать заказ в кабинете;
else (нет)
  :Продолжить поиск в каталоге;
endif

stop
@enduml
```

### 19.3. BPMN-подобная диаграмма процесса покупки

```plantuml
@startuml
|Покупатель|
start
:Открыть карточку товара;
:Выбрать размер / вариант;

|Frontend / система|
:Запросить товар и рекомендацию;

|Backend API|
:Проверить наличие товара;
:Собрать fit-profile пользователя;
:Рассчитать рекомендацию размера;

if (fit-profile неполный?) then (да)
  :Сформировать low confidence;
  :Добавить warning;
endif

if (Точного размера нет?) then (да)
  :Выбрать ближайший размер;
  :Добавить warning;
endif

if (Стиль / сезон не совпадает?) then (да)
  :Добавить warning;
endif

|Frontend / система|
:Показать size recommendation,\nexplanation и capsule outfit;

|Покупатель|
:Добавить товар в корзину;
:Перейти к оформлению;

|Backend API|
:Создать заказ;
:Создать платёжную сессию;

|Платёжный провайдер|
:Провести оплату;

if (Оплата успешна?) then (да)
  |Backend API|
  :Обновить статус заказа = paid;
  |Склад / менеджер заказов|
  :Собрать заказ;
  :Упаковать заказ;
  |Служба доставки|
  :Принять отправление;
  :Доставить заказ;
  |Покупатель|
  :Получить заказ;
  stop
else (нет)
  |Frontend / система|
  :Показать ошибку оплаты;
  |Покупатель|
  :Повторить оплату или отменить;
  stop
endif
@enduml
```

### 19.4. DFD Context Diagram (Level 0)

```plantuml
@startuml
skinparam componentStyle rectangle

actor "Покупатель" as Customer
actor "Администратор" as Admin
actor "Платёжный\nпровайдер" as PaymentProvider
actor "Служба\nдоставки" as DeliveryService

rectangle "Система AnimeAttire" as System

Customer --> System : запросы каталога,\nданные профиля,\nкорзина и заказ
System --> Customer : товары, рекомендации,\nстатусы заказа

Admin --> System : управление товарами,\nкатегориями, заказами
System --> Admin : данные каталога,\nстатусы и аналитика

System --> PaymentProvider : платёжная сессия,\nданные оплаты
PaymentProvider --> System : статус оплаты

System --> DeliveryService : данные отправки
DeliveryService --> System : статусы доставки
@enduml
```

### 19.5. DFD Level 1

```plantuml
@startuml
skinparam componentStyle rectangle

actor "Покупатель" as Customer
actor "Администратор" as Admin
actor "Платёжный провайдер" as PaymentProvider
actor "Служба доставки" as DeliveryService

rectangle "Управление\nаккаунтом" as P1
rectangle "Управление\nfit-profile" as P2
rectangle "Каталог и карточка\nтовара" as P3
rectangle "Recommendation\nengine" as P4
rectangle "Корзина" as P5
rectangle "Checkout /\nOrders" as P6
rectangle "Payments" as P7
rectangle "Delivery tracking" as P8
rectangle "Admin catalog\nmanagement" as P9

database "User DB" as D1
database "Catalog DB" as D2
database "Orders DB" as D3
database "Payments DB" as D4

Customer --> P1 : регистрация,\nавторизация
Customer --> P2 : параметры фигуры,\nстиль, сезон
Customer --> P3 : просмотр каталога,\nкарточка товара
Customer --> P5 : действия с корзиной
Customer --> P6 : оформление заказа

P1 <--> D1
P2 <--> D1
P3 <--> D2
P4 <--> D1
P4 <--> D2
P5 <--> D2
P5 <--> D3
P6 <--> D3
P7 <--> D4
P8 <--> D3
P9 <--> D2

P3 --> P4 : товар + fit-profile
P4 --> P3 : size recommendation,\nexplanation, warnings,\ncapsule outfit

P6 --> P7 : запрос на оплату
P7 --> PaymentProvider : платёжные данные
PaymentProvider --> P7 : результат оплаты
P7 --> P6 : статус оплаты

P6 --> P8 : заказ к доставке
P8 --> DeliveryService : данные отправки
DeliveryService --> P8 : статусы доставки

Admin --> P9 : CRUD каталога
Admin --> P6 : управление заказами
@enduml
```

### 19.6. ERD

```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "User" as User {
  * id : bigint
  --
  username : varchar
  email : varchar
  phone : varchar
  fit_profile : json
  fit_profile_updated_at : datetime
}

entity "Address" as Address {
  * id : bigint
  --
  user_id : bigint
  city : varchar
  street : varchar
}

entity "Category" as Category {
  * id : bigint
  --
  name : varchar
  slug : varchar
}

entity "AnimeFranchise" as Franchise {
  * id : bigint
  --
  name : varchar
  slug : varchar
}

entity "Product" as Product {
  * id : bigint
  --
  category_id : bigint
  franchise_id : bigint
  name : varchar
  slug : varchar
  price : decimal
  is_active : bool
  is_featured : bool
}

entity "ProductVariant" as Variant {
  * id : bigint
  --
  product_id : bigint
  size : varchar
  stock : int
  is_active : bool
}

entity "ProductImage" as ProductImage {
  * id : bigint
  --
  product_id : bigint
  image : varchar
  is_primary : bool
}

entity "ProductTag" as ProductTag {
  * id : bigint
  --
  name : varchar
  slug : varchar
}

entity "ProductRelation" as ProductRelation {
  * id : bigint
  --
  source_product_id : bigint
  target_product_id : bigint
  relation_type : varchar
}

entity "Cart" as Cart {
  * id : bigint
  --
  user_id : bigint
}

entity "CartItem" as CartItem {
  * id : bigint
  --
  cart_id : bigint
  variant_id : bigint
  quantity : int
}

entity "Order" as Order {
  * id : bigint
  --
  user_id : bigint
  status : varchar
  total_amount : decimal
}

entity "OrderItem" as OrderItem {
  * id : bigint
  --
  order_id : bigint
  variant_id : bigint
  quantity : int
  price : decimal
}

entity "DeliveryMethod" as DeliveryMethod {
  * id : bigint
  --
  name : varchar
  price : decimal
}

entity "OrderDeliverySnapshot" as DeliverySnapshot {
  * id : bigint
  --
  order_id : bigint
  delivery_method_id : bigint
}

entity "DeliveryTrackingEvent" as TrackingEvent {
  * id : bigint
  --
  order_id : bigint
  status : varchar
  occurred_at : datetime
}

entity "PaymentMethod" as PaymentMethod {
  * id : bigint
  --
  name : varchar
}

entity "Payment" as Payment {
  * id : bigint
  --
  order_id : bigint
  payment_method_id : bigint
  status : varchar
  amount : decimal
}

entity "PaymentEvent" as PaymentEvent {
  * id : bigint
  --
  payment_id : bigint
  event_type : varchar
}

entity "PaymentRefund" as Refund {
  * id : bigint
  --
  payment_id : bigint
  amount : decimal
}

entity "FavoriteProduct" as FavoriteProduct {
  * id : bigint
  --
  user_id : bigint
  product_id : bigint
}

entity "ContactRequest" as ContactRequest {
  * id : bigint
  --
  user_id : bigint
  message : text
}

User ||--o{ Address
User ||--o| Cart
User ||--o{ Order
User ||--o{ FavoriteProduct
User ||--o{ ContactRequest

Category ||--o{ Product
Franchise ||--o{ Product
Product ||--o{ Variant
Product ||--o{ ProductImage
Product ||--o{ ProductRelation : source
Product ||--o{ ProductRelation : target
Product }o--o{ ProductTag
Product ||--o{ FavoriteProduct

Cart ||--o{ CartItem
Variant ||--o{ CartItem

Order ||--o{ OrderItem
Variant ||--o{ OrderItem
Order ||--o| DeliverySnapshot
DeliveryMethod ||--o{ DeliverySnapshot
Order ||--o{ TrackingEvent

Order ||--o{ Payment
PaymentMethod ||--o{ Payment
Payment ||--o{ PaymentEvent
Payment ||--o{ Refund
@enduml
```

### 19.7. Sequence Diagram: заполнение fit-profile

```plantuml
@startuml
actor "Покупатель" as Customer
participant "Account UI" as UI
participant "API" as API
participant "User serializer /\nservice" as UserService
database "User DB" as DB

Customer -> UI : Открывает раздел fit-profile
UI -> API : GET /users/me/
API -> DB : Получить профиль пользователя
DB --> API : User + fit_profile
API --> UI : Текущие данные профиля

Customer -> UI : Вводит рост, вес, мерки,\nstyle, season, preferred fit
UI -> API : PATCH /users/me/fit-profile
API -> UserService : validate(payload)
UserService -> UserService : Проверка диапазонов\nи структуры JSON
UserService -> DB : Сохранить fit_profile\nи fit_profile_updated_at
DB --> UserService : OK
UserService --> API : Обновлённый профиль
API --> UI : 200 OK + fit_profile
UI --> Customer : Показать сообщение "Профиль сохранён"
@enduml
```

### 19.8. Sequence Diagram: recommendation в карточке товара

```plantuml
@startuml
actor "Покупатель" as Customer
participant "Product Detail UI" as UI
participant "Catalog API" as API
participant "Recommendation\nservice" as Service
database "Catalog DB" as CatalogDB
database "User DB" as UserDB

Customer -> UI : Открывает карточку товара
UI -> API : GET /products/{slug}
API -> CatalogDB : Загрузить товар,\nварианты, изображения, теги
CatalogDB --> API : Product data

alt Пользователь авторизован
  API -> UserDB : Загрузить fit_profile
  UserDB --> API : fit_profile
  API -> Service : buildRecommendation(product, fit_profile)
  Service -> CatalogDB : Получить активные размеры\nи связанные товары
  CatalogDB --> Service : variants + relations
  Service -> Service : Выбрать размер,\nconfidence, warnings,\nexplanation, capsule outfit
  Service --> API : recommendation response
else Гость
  API -> Service : buildGuestRecommendation(product)
  Service --> API : базовая рекомендация /\nнизкая точность
end

API --> UI : Product detail + fit_recommendation
UI --> Customer : Показать размер,\nобъяснение, warnings,\nкапсульный образ
@enduml
```

### 19.9. Sequence Diagram: checkout

```plantuml
@startuml
actor "Покупатель" as Customer
participant "Checkout UI" as UI
participant "Orders API" as API
participant "Payments service" as Payments
participant "Платёжный\nпровайдер" as PSP
database "Orders DB" as OrdersDB

Customer -> UI : Подтверждает корзину
UI -> API : POST /orders/checkout
API -> OrdersDB : Создать order + order_items
OrdersDB --> API : order_id
API -> Payments : createPaymentSession(order)
Payments -> PSP : Инициализировать оплату
PSP --> Payments : payment_url / status=pending
Payments --> API : payment session
API --> UI : order + payment_url

Customer -> PSP : Выполняет оплату
PSP -> Payments : webhook / payment result
Payments -> OrdersDB : Сохранить payment,\npayment_events,\nобновить order status
OrdersDB --> Payments : OK

Customer -> UI : Возвращается на сайт
UI -> API : GET /orders/{id}
API -> OrdersDB : Получить актуальный статус
OrdersDB --> API : status = paid / failed
API --> UI : Данные заказа
UI --> Customer : Показать статус оплаты
@enduml
```

### 19.10. Component Diagram

```plantuml
@startuml
skinparam componentStyle rectangle

package "Frontend (Next.js)" {
  [Home Page]
  [Catalog Page]
  [Product Detail Page]
  [Cart Drawer]
  [Checkout Page]
  [Account Page]
}

package "Backend (Django / DRF)" {
  [Auth API]
  [Users API]
  [Catalog API]
  [Orders API]
  [Payments API]
  [Recommendation Service]
  [Admin Panel]
}

database "PostgreSQL" as DB
[Payment Provider] as PSP
[Delivery Service] as Delivery

[Home Page] --> [Catalog Page]
[Catalog Page] --> [Catalog API]
[Product Detail Page] --> [Catalog API]
[Product Detail Page] --> [Recommendation Service]
[Cart Drawer] --> [Orders API]
[Checkout Page] --> [Orders API]
[Checkout Page] --> [Payments API]
[Account Page] --> [Users API]

[Catalog API] --> [Recommendation Service]
[Auth API] --> DB
[Users API] --> DB
[Catalog API] --> DB
[Orders API] --> DB
[Payments API] --> DB
[Admin Panel] --> DB
[Payments API] --> PSP
[Orders API] --> Delivery
@enduml
```

### 19.11. Deployment Diagram

```plantuml
@startuml
node "Пользовательское устройство" as Client {
  artifact "Browser"
}

node "Vercel / Frontend hosting" as FrontendHost {
  artifact "Next.js frontend"
}

node "Backend server" as BackendHost {
  artifact "Django + DRF API"
  artifact "Admin panel"
}

database "PostgreSQL" as Postgres
node "Payment provider" as PSP
node "Delivery provider" as Delivery

Client --> FrontendHost : HTTPS
FrontendHost --> BackendHost : REST API / HTTPS
BackendHost --> Postgres : SQL
BackendHost --> PSP : Payment API / webhooks
BackendHost --> Delivery : Delivery status API
@enduml
```

### 19.12. State Machine Diagram: заказ

```plantuml
@startuml
[*] --> pending

pending --> paid : оплата подтверждена
pending --> cancelled : отмена / таймаут

paid --> picking : заказ передан на сборку
paid --> cancelled : отмена до сборки

picking --> packed : товары собраны
picking --> cancelled : отмена менеджером

packed --> shipped : передано в доставку
packed --> returned : возврат до отправки

shipped --> delivered : заказ доставлен
shipped --> returned : возврат / недоставка

delivered --> returned : оформлен возврат

cancelled --> [*]
returned --> [*]
delivered --> [*]
@enduml
```

### 19.13. Activity Diagram: алгоритм рекомендации размера

```plantuml
@startuml
start
:Получить товар и пользователя;

if (Пользователь авторизован?) then (да)
  :Загрузить fit-profile;
else (нет)
  :Использовать guest-mode;
endif

if (fit-profile заполнен?) then (да)
  :Определить тип товара\n(верх / низ / универсальный);
  :Получить активные размеры;
  if (Размеры доступны?) then (да)
    :Учесть рост, вес, мерки,\nобычный размер,\npreferred fit и fit товара;
    :Найти ближайший подходящий размер;
    if (Точный размер найден?) then (да)
      :Установить основной recommendation;
    else (нет)
      :Выбрать ближайший размер;
      :Добавить warning "лучше взять другой размер";
    endif
    :Рассчитать confidence;
    :Сформировать explanation;
  else (нет)
    :Вернуть "рекомендация недоступна";
  endif
else (нет)
  :Сформировать low confidence;
  :Добавить warning "заполните fit-profile";
endif

if (Стиль / сезон не совпадает?) then (да)
  :Добавить тематический warning;
endif

:Подобрать капсульный образ;
:Собрать recommendation response;
stop
@enduml
```

### 19.14. Activity Diagram: подбор капсульного образа

```plantuml
@startuml
start
:Взять основной товар;
:Проверить ProductRelation;

if (Есть связанные товары?) then (да)
  :Использовать связанные позиции;
else (нет)
  :Взять fallback по франшизе,\nкатегории и тегам;
endif

:Убрать дубли категорий;
:Отфильтровать неактивные\nи отсутствующие в наличии товары;

if (У пользователя есть бюджет?) then (да)
  :Отсечь слишком дорогие товары;
endif

if (У пользователя есть стиль / сезон?) then (да)
  :Приоритизировать совпадающие товары;
endif

:Собрать 2-3 совместимых позиции;
:Посчитать итоговую сумму;
:Сформировать explanation для capsule outfit;
stop
@enduml
```

### 19.15. Sitemap / структура экранов

```plantuml
@startmindmap
* AnimeAttire
** Главная
** Каталог
*** Фильтры
*** Поиск
*** Теги
** Карточка товара
*** Галерея
*** Размеры и варианты
*** Recommendation block
*** Capsule outfit
** Корзина
** Checkout
** Личный кабинет
*** Профиль
*** Адреса
*** Fit-profile
*** Заказы
*** Избранное
** Контакты
** Доставка и возврат
** Политика и оферта
** В перспективе
*** Wizard smart fitting
*** Рекомендации в каталоге
*** История рекомендаций
@endmindmap
```
