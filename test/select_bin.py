import cv2

# путь к изображению
image_path = r"C:\Users\vwork\PycharmProjects\upura_test_pipeline\test\test_task_001_1_roi.jpg"  # Замени на свой файл

# загрузка изображения
img = cv2.imread(image_path)

# перевод в grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# функция для trackbar (обязательная, но ничего не делает)
def nothing(x):
    pass

# окно
cv2.namedWindow("Binary Tuning")

# создаём ползунок
cv2.createTrackbar("Threshold", "Binary Tuning", 127, 255, nothing)

while True:
    # читаем значение ползунка
    thresh_value = cv2.getTrackbarPos("Threshold", "Binary Tuning")

    # бинаризация
    _, binary = cv2.threshold(gray, thresh_value, 255, cv2.THRESH_BINARY)

    # показываем изображения
    cv2.imshow("Original", gray)
    cv2.imshow("Binary Tuning", binary)

    # выход по ESC
    key = cv2.waitKey(1)
    if key == 27:
        break

cv2.destroyAllWindows()