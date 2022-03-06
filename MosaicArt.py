import os
import cv2
import numpy as np
import random

#入力
main_name = "gm.jpg"  #メイン画像名
sub_name = "Sub_Photos"  #サブ画像ファイル名

# Main photo
mainPhoto = cv2.imread(main_name)
#height, width
h, w = mainPhoto.shape[:2]
# Sub photos
subPhotos = [os.path.join(sub_name, i) for i in os.listdir(sub_name)]


#分割数は等しく、作成画像の比率をキープ
y_divide = 64    #heightの分割数
x_divide = y_divide   #widthの分割数
y_size_result = 3000    #作成画像のheight
x_size_result = int(y_size_result*w/h)    #作成画像のheightに対し、比率を維持したwidth
result_filename = "mozaikuArt_test" #作成ファイル名(.jpgなし)
variation_bgr = 0.5 #bgr調整量0~1




# 平均明度
def average_brightness(img):
    return int(img.mean())

# 平均彩度
def average_saturation(img):
    b = int(img[:, :, 0].mean())
    g = int(img[:, :, 1].mean())
    r = int(img[:, :, 2].mean())
    return b, g, r

# HSVList
def average_HSV(img):
    img_hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    h = int(img_hsv[:, :, 0].mean())
    s = int(img_hsv[:, :, 1].mean())
    v = int(img_hsv[:, :, 2].mean())
    return [h,s,v]
    
    
# (一度使った画像は使い切るまで使わない)元画像とサブ画像を対応付けて、サブ画像の並び順を決定する。
def decide_order(a_elements, b_elements, as_hsv):
    #順番
    lost_b_elements = np.array(b_elements)
    counter = len(b_elements)
    name = 0

    for a_n in range(len(a_elements)):
        a_element = a_elements[a_n]
        # if b>200, g>200, r<100, random
        if a_element[1] > 200 and a_element[2] > 200 and a_element[3] < 100:
            number = random.randint(0,len(b_elements)-1)
            img = cv2.imread(subPhotos[number])
            
            img_hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
            img_hsv[:,:,(1)] = np.clip(img_hsv[:,:,(1)]*0.9, 0, 255) # 彩度の計算
            img_hsv[:,:,(2)] = np.clip(img_hsv[:,:,(2)]*0.9, 50, 200) # 明度の計算
            img_bgr = cv2.cvtColor(img_hsv,cv2.COLOR_HSV2BGR)
            cv2.imwrite("NEWSub_Photos/%s.jpg" % str(name).zfill(8),img_bgr)
            name += 1
        else:
            if counter <= 200:
                counter = len(b_elements)
                lost_b_elements = np.array(b_elements)
            scoreList = [a_element - b_element for b_element in lost_b_elements]    
            scores = [sum(abs(score)) for score in scoreList]
            scores_index = scores.index(min(scores))

            #　RGB&HSVの変更
            a_av_hsv = np.array(as_hsv[a_n])
            b_img = cv2.imread(subPhotos[scores_index])
            variation = scoreList[scores_index]

            b_img[:,:,(0)] = np.clip(b_img[:,:,(0)]*(1+variation_bgr*variation[1]/255), 0, 255) # B
            b_img[:,:,(1)] = np.clip(b_img[:,:,(1)]*(1+variation_bgr*variation[2]/255), 0, 255) # G
            b_img[:,:,(2)] = np.clip(b_img[:,:,(2)]*(1+variation_bgr*variation[3]/255), 0, 255) # R

            b_hsv = cv2.cvtColor(b_img,cv2.COLOR_BGR2HSV)
            b_av_hsv = np.array(average_HSV(b_img))
            a_sub_b = a_av_hsv - b_av_hsv #(H,S,V)
            
            b_hsv[:,:,(0)] = np.clip(b_hsv[:,:,(0)], 0, 180) # 色相の計算
            b_hsv[:,:,(1)] = np.clip(b_hsv[:,:,(1)]*(1+a_sub_b[1]/255), 0, 255) # 彩度の計算
            b_hsv[:,:,(2)] = np.clip(b_hsv[:,:,(2)]*(1+a_sub_b[2]/255), 0, 255) # 明度の計算
            
            b_bgr = cv2.cvtColor(b_hsv,cv2.COLOR_HSV2BGR)
            cv2.imwrite("NEWSub_Photos/%s.jpg" % str(name).zfill(8),b_bgr)
            name += 1

            lost_b_elements[scores_index] = np.array([501,501,501,501])
            counter -= 1



# mainの分割した画像をRGBでリスト化
mainList = []
mainEler = 0
main_hsv = []
x0 = int(w/y_divide)
y0 = int(h/x_divide)
for y in range(y_divide):
    for x in range(x_divide):
        tmp = mainPhoto[y0*y:y0*(y+1), x0*x:x0*(x+1)]
        if tmp is not None:
            b, g, r = average_saturation(tmp)
            brightness = average_brightness(tmp)
            mainList.append(np.array([brightness, b, g, r]))
            #HSVの追加
            main_hsv.append(average_HSV(tmp))

        else:
            mainEler += 1
print('mainエラー数:',mainEler)

# sub画像をRGBでリスト化
subList = []
subElerList = []
subEler = 0
for i in range(len(subPhotos)):
    tmp = cv2.imread(subPhotos[i])
    if tmp is not None:
        brightness = average_brightness(tmp)
        b, g, r = average_saturation(tmp)
        subList.append(np.array([brightness, b, g, r]))
    else:
        subEler += 1
        subElerList.append(subPhotos[i])
print('subエラー数:',subEler)

#エラーの出た写真の消去
for i in subElerList:
    subPhotos.remove(i)

decide_order(mainList,subList,main_hsv)
# newPhotosを作成
newPhotos = [os.path.join("NEWSub_Photos", i) for i in os.listdir("NEWSub_Photos")]

# NEWSub_Photosのうち、画像にできないものを消去
newElerList = []
newEler = 0
for i in range(len(newPhotos)):
    tmp = cv2.imread(newPhotos[i])
    if tmp is None:
        newEler += 1
        newElerList.append(newPhotos[i])
print('newエラー数:',newEler)
if newEler > 0:
    for i in newElerList:
        newPhotos.remove(i)
newPhotos.sort()

# モザイクアートの下地を生成する。
img_result = np.zeros((y_size_result, x_size_result, 3), dtype=np.uint8)
y_size = int(y_size_result/y_divide)
x_size = int(x_size_result/x_divide)

# orderListの順番通りに
orderEler = 0
if subEler <= 10:
    for y in range(y_divide):
        for x in range(x_divide):
            img = cv2.imread(newPhotos[x+x_divide*y])
            if img is not None:
                #cv.resizeは(width, height)(x_size, y_size)
                img = cv2.resize(img, (x_size, y_size))
                img_result[y*y_size:(y+1)*y_size, x*x_size:(x+1)*x_size] = img
            else:
                orderEler += 1
    print('orderListエラー数:',orderEler)
    cv2.imwrite(os.path.join('PhotoFile', '{}.jpg'.format(result_filename)), img_result)

