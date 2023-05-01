from flask import Flask, request, jsonify, url_for
from PIL import Image
from classifier import clasiffier_CNN_predict
from gfp_gan_api import predict_gfpgan_image
from image_functions import b64_2_img, im_2_b64, get_as_base64, get_as_im
from image_inpainting_api import predict_image_inpainting

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

@app.route('/getfilename', methods=['POST'])
def show_file_name():
    # get image filename
    get_file_img = request.files['filename']

    file_name = secure_filename(get_file_img.filename)

    full_file_name = "." + url_for("static", filename="images/" + file_name)

    #open file as a PIL object, resize, convert to RGB(x,x,3) and save path
    imgPILresized = Image.open(get_file_img).resize((512, 512))
    imgPILresized = imgPILresized.convert('RGB')
    imgPILresized.save(full_file_name, 'JPEG')

    #Convert Image to b64
    img_b64 = im_2_b64(imgPILresized)

    #Enviar PIL Object al clasificador
    result_casiffier = clasiffier_CNN_predict(imgPILresized)

    if(result_casiffier == "Imagen Borrosa"):
        # Enviar filepath to gfp-gan api
        predicted_gfpgan_image_url = predict_gfpgan_image(full_file_name)

        # convert url_gfp_gan_output to base64
        base64_predicted_gfpgan = get_as_base64(predicted_gfpgan_image_url)
    elif (result_casiffier == "Imagen Agrietada"):
        # Enviar filepath to image_inpainting api
        predicted_inpainting_url = predict_image_inpainting(full_file_name)

        # convert url_inpainting_output to base64
        base64_predicted_inpainting = get_as_base64(predicted_inpainting_url)
    else:
        # Enviar filepath to image_inpainting api
        predicted_inpainting_url = predict_image_inpainting(full_file_name)

        # convert url_inpainting_output to base64
        base64_predicted_inpainting = get_as_base64(predicted_inpainting_url)

        #Convertir url to PIL Image, convert to RGB(3 dim) y sobreescribir el archivo con el resultado
        img_inpainted = get_as_im(predicted_inpainting_url)
        img_inpainted = img_inpainted.convert('RGB')
        img_inpainted.save(full_file_name, 'JPEG')

        # Enviar filepath to gfp-gan api
        predicted_gfpgan_image_url = predict_gfpgan_image(full_file_name)

        # convert url_gfp_gan_output to base64
        base64_predicted_gfpgan = get_as_base64(predicted_gfpgan_image_url)


    return jsonify({'status': 'base64 recibida correctamente', 'base64': img_b64, 'imageResult': result_casiffier, 'GFP-GAN': base64_predicted_gfpgan, 'Inpainting': base64_predicted_inpainting})


@app.route('/')
def index():
    return jsonify({"Test":"Hola"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
