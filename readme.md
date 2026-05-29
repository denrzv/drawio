# Общее описание

Проект предназначен для автоматизации проверки drawio диаграм, использующих стандарт C4, а так же созданеи модели по диаграмме в формате Structurizr DSL

Реализованы следующие проверки:

* Заполненность описаний компонент
* Заполненность технологий компонент
* Заполненность описаний связей.
  С*вязи изображают вызовы между компонентами.  На связях между компонентами указываются данные которые передаются от компонента к компоненту.** **
  Используется следующая нотация:* *название действия (передаваемые данные): возвращаемые данные [технологии]
  Например* *”Зарегистрировать заказ (абонент, продукт): заказ [*  *gRPC* *]»*
* Заполненность технологий связей

поддерживается как сжатый так и обычный формат drawio

Скрипит пытается исправить следующие проблемы в фалйах:

* Когда стрелки не присоеденены к объекту а только касаются
* Когда стрелки не являются стрелаками в нотации C4

# Инсталяция

* Для работы потребуется python3
* Для экспорта Structurizr DSL используются только модули стандартной библиотеки Python 3.


# Использование

```sh
python3 drawio_parser.py -i <inputfile> [-i <inputfile> ...] [-d] [-s] [-H]
```

Пример для Ubuntu 22:

```sh
python3 drawio_parser.py -i input.drawio -d -s
```

inputfile - имя файла в формате drawio. Можно указать несколько `-i`, чтобы объединить системный контекст и контейнерные диаграммы в одну модель.

Результат всегда записывается в файл `workspace.dsl` в текущем каталоге.

d - проверка синтаксиса входных и выходных данных

s - печать статистики

H - иерархический экспорт: дополнительно создаёт каталог `relationships/` со связями системного контекста и контейнерных диаграмм, а также каталог `views/` с DSL-файлами представлений. Основной `workspace.dsl` подключает эти файлы через `!include`.

# Маркерные теги Structurizr

Конвертер поддерживает нейтральные цветовые маркеры для переноса change-notation из draw.io в Structurizr DSL. Бизнес-смысл цветов не зашит в код: проект сам решает, что означает каждый цвет.

SVG-иконки находятся в каталоге `assets/structurizr/icons/markers/`:

* `marker-green.svg`
* `marker-red.svg`
* `marker-blue.svg`
* `marker-gray.svg`
* `marker-purple.svg`

Поддерживаемые теги элементов:

* `Marker:Green`
* `Marker:Red`
* `Marker:Blue`
* `Marker:Gray`
* `Marker:Purple`

Тег можно назначить вручную в DSL:

```dsl
themesBff = container "Themes BFF" "Provides themes for operator" "Spring Boot" {
    tags "Marker:Red"
}
```

Если в экспортируемых элементах есть маркерные теги, конвертер добавляет в секцию `views` стили с локальными SVG-иконками:

```dsl
styles {
    element "Marker:Green" {
        icon ./assets/structurizr/icons/markers/marker-green.svg
    }
}
```

## Маппинг метаданных draw.io в маркерные теги

По умолчанию маркеры отключены, поэтому существующий экспорт не меняется. Чтобы включить стандартный маппинг свойства `changeStatus`, запустите конвертер с флагом `--marker-tags`:

```sh
python3 drawio_parser.py -i input.drawio -d -s --marker-tags
```

Стандартный маппинг:

* `unchanged` -> `Marker:Blue`
* `changed` -> `Marker:Green`
* `created` -> `Marker:Red`
* `deprecated` -> `Marker:Gray`
* `special` -> `Marker:Purple`

Имя свойства draw.io можно изменить без JSON-файла:

```sh
python3 drawio_parser.py -i input.drawio --marker-tags --marker-property status
```

Также можно передать JSON-конфигурацию:

```json
{
  "enabled": true,
  "drawioPropertyName": "changeStatus",
  "mapping": {
    "unchanged": "Marker:Blue",
    "changed": "Marker:Green",
    "created": "Marker:Red",
    "deprecated": "Marker:Gray",
    "special": "Marker:Purple"
  }
}
```

```sh
python3 drawio_parser.py -i input.drawio --marker-tags-config marker-tags.json
```

Маркерные теги добавляются к существующим тегам элемента и не перезаписывают их.

Ограничение: Structurizr DSL поддерживает один `icon` в стиле элемента и не даёт точно позиционировать маркер как badge в правом нижнем углу. Поэтому маркерная иконка отображается как основная иконка элемента и может конфликтовать с технологическими иконками.
