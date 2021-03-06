from utils.builder import Builder
import tensorflow as tf
from utils.Base_Archs.Base_Segnet import Base_Segnet

class FRRN_C(Base_Segnet):
    def __init__(self, kwargs):
        super().__init__(kwargs)

    def build_net(self):
        '''
        F-Net, based off FRRN, replaced encode-decode block with Atrous convolutions, reduced network size, enclosed FRRU sequence within pool-upscale block
        '''
        with tf.name_scope('FRRN_C'):
            with Builder(**self.build_params) as frnn_c_builder:

                #Setting control params
                frnn_c_builder.control_params(Dropout_control=self.dropout_placeholder, State=self.state_placeholder)

                #Construct functional building blocks
                def RU(input, filters):
                    with tf.name_scope('Residual_Unit'):
                        Conv1 = frnn_c_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv2 = frnn_c_builder.Conv2d_layer(Conv1, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv3 = frnn_c_builder.Conv2d_layer(Conv2, k_size=[5, 5], stride=[1, 1, 1, 1], filters=filters, Activation=False)

                        return frnn_c_builder.Residual_connect([input, Conv3])


                def FRRU(Residual_stream, Pooling_stream, scale_factor, filters, res_filters=32, D_rate=1, k_size=[3,3]):
                    with tf.name_scope('Full_Resolution_Unit'):
                        scale_dims = [1, scale_factor, scale_factor, 1]
                        Pool = frnn_c_builder.Pool_layer(Residual_stream, k_size=scale_dims, stride=scale_dims)

                        Concat = frnn_c_builder.Concat([Pool, Pooling_stream])

                        Conv0 = frnn_c_builder.Conv2d_layer(Concat, stride=[1,1,1,1], k_size=[1,1], filters=filters, Batch_norm=True)
                        Conv1 = frnn_c_builder.DConv_layer(Conv0,  filters=filters, Batch_norm=True, D_rate=D_rate)
                        Conv2 = frnn_c_builder.DConv_layer(Conv1, filters=filters, Batch_norm=True, D_rate=D_rate)

                        Res_connect = frnn_c_builder.Residual_connect([Conv0, Conv2])

                        Conv3 = frnn_c_builder.Conv2d_layer(Res_connect, k_size=[1, 1], stride=[1, 1, 1, 1], filters=res_filters, Activation=False, Batch_norm=True)

                        Unpool = frnn_c_builder.Conv_Resize_layer(Conv3, k_size=k_size, output_scale=scale_factor, Batch_norm=False )
                    Residual_stream_out = frnn_c_builder.Concat([Residual_stream, Unpool])
                    Pooling_stream_out = Res_connect
                    return Residual_stream_out, Pooling_stream_out


                #Model Construction
                with tf.name_scope('First_half'):
                    Stem = frnn_c_builder.Conv2d_layer(self.input_placeholder, stride=[1, 1, 1, 1], k_size=[3, 3], filters=64, Batch_norm=True)
                    Stem_pool = frnn_c_builder.Pool_layer(Stem)
                
                    Stem_pool = RU(Stem_pool, 64)
                    Stem_pool = RU(Stem_pool, 64)

                    Residual_stream = frnn_c_builder.Conv2d_layer(Stem_pool, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                    Pooling_stream = frnn_c_builder.Pool_layer(Stem_pool)

                    #Encoder
                    scale_factor = 2
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=32, D_rate=2)
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=32, D_rate=4)
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=64, D_rate=8)
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=64, D_rate=16)
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=256, D_rate=32)
                    Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=256, D_rate=32, k_size=[5,5])



                    Pooling_stream = Pooling_stream = frnn_c_builder.Conv_Resize_layer(Pooling_stream, k_size=[3, 3], Batch_norm=True, output_scale=2)
                    RP_stream_merge = frnn_c_builder.Concat([Pooling_stream, Residual_stream])
                    Conv3 = frnn_c_builder.Conv2d_layer(RP_stream_merge, stride=[1, 1, 1, 1], k_size=[1, 1], filters=64, Batch_norm=True)
                    Upconv = frnn_c_builder.Conv_Resize_layer(Conv3, stride=[1,1,1,1],Batch_norm=True,Activation=False,k_size=[3, 3], filters=64)
                    Res_connect = frnn_c_builder.Residual_connect([Stem, Upconv])
                    Res_connect = RU(Res_connect, 64)
                output = frnn_c_builder.Conv2d_layer(Res_connect, filters=1, stride=[1, 1, 1, 1], k_size=[1, 1], Batch_norm=False, Activation=False)
                return output

    def construct_loss(self):
        super().construct_loss()
        output = tf.reshape(self.output, shape=(-1, self.build_params['Image_width'] * self.build_params['Image_height']))
        output_placeholder = tf.reshape(self.output_placeholder, shape=(-1, self.build_params['Image_width'] * self.build_params['Image_height']))
        Probs = tf.nn.sigmoid(output)
        offset = 1e-5
        Threshold = 0.1
        Probs_processed = tf.clip_by_value(Probs, offset, 1.0)
        Con_Probs_processed = tf.clip_by_value(1-Probs, offset, 1.0)
        W_I = (-output_placeholder * tf.log(Probs_processed) - (1 - output_placeholder)*tf.log(Con_Probs_processed))
        Weighted_BCE_loss = tf.reduce_sum(W_I) / tf.cast(tf.maximum(tf.count_nonzero(W_I -Threshold),0), tf.float32)
        tf.summary.scalar('WBCE loss', Weighted_BCE_loss)
        tf.summary.image('WCBE', tf.reshape(W_I, [-1, self.build_params['Image_width'], self.build_params['Image_height'], 1]))
        self.loss.append(Weighted_BCE_loss)
    '''

                with tf.name_scope('Focal_Loss'):
                    
                    P = tf.minimum(tf.nn.sigmoid(logits)+1e-4,1.0) #safe for log sigmoid
                    F1= -output_placeholder*tf.pow(1-P,5)*tf.log(P) -(1-output_placeholder)*tf.pow(P,5)*tf.log(1-P+1e-4)
                    tf.summary.image('FOCAL Loss', tf.reshape(F1,[1, 1024, 1024, 1]))
                    F1_count = tf.count_nonzero(tf.maximum(F1-0.05,0))
                    #final_focal_loss = tf.multiply(tf.reduce_mean(F1),1)
                    final_focal_loss = tf.multiply(tf.reduce_sum(F1)/ tf.to_float(tf.maximum(F1_count, 1024*5)), 1)
                    tf.summary.scalar('Count focal loss', F1_count)
                    tf.summary.scalar('Focal losssum ', tf.reduce_sum(F1))
                    #focal_loss = tf.multiply(tf.multiply(Y, tf.square(1 - P)),L) + tf.multiply(tf.multiply(1-Y, tf.square(P)),max_x+L)
                    #final_focal_loss = tf.reduce_mean(focal_loss)
                    #eps = tf.constant(value=1e-5)
                    #sigmoid = tf.nn.sigmoid(logits) + eps
                
                
                with tf.name_scope('BCE_Loss'):
                    offset = 1e-5
                    Threshold = 0.1
                    Probs = tf.nn.sigmoid(logits)
                    Wmask = tf.multiply( 1- tf.floor(Probs+Threshold), output_placeholder)
                    Probs_processed = tf.clip_by_value(Probs, offset, 1.0)
                    Con_Probs_processed = tf.clip_by_value(1-Probs, offset, 1.0)
                    W_I = (-Wmask * tf.log(Probs_processed) - (1-output_placeholder)*tf.log(Con_Probs_processed))
                    Weighted_BCE_loss = tf.reduce_sum(W_I) /( tf.reduce_sum(Wmask)+100)
                    EU_loss =tf.losses.huber_loss(output_placeholder, Probs)

                #Dice Loss
                with tf.name_scope('Dice_Loss'):

                    eps = tf.constant(value=1e-5, name='eps')
                    sigmoid = tf.nn.sigmoid(output,name='sigmoid') + eps
                    sigmoid =tf.reshape(sigmoid, shape= [-1, kwargs['Image_width']*kwargs['Image_height']])
                    intersection =sigmoid * output_placeholder 
                    union = tf.reduce_sum(intersection,1) / ( tf.reduce_sum(sigmoid , 1, name='reduce_sigmoid') + tf.reduce_sum(output_placeholder ,1,name='reduce_mask') + 1e-5)
                    Dice_loss = 2. *  (union)
                    Dice_loss = 1 - tf.reduce_mean(Dice_loss,name='diceloss')
                    
                
                #Graph Exports
                tf.add_to_collection(kwargs['Model_name'] + '_Input_ph', input_placeholder)
                tf.add_to_collection(kwargs['Model_name'] + '_Input_reshape', input_reshape)
                tf.add_to_collection(kwargs['Model_name'] + '_Weight_ph', weight_placeholder)
                tf.add_to_collection(kwargs['Model_name'] + '_Output_ph', output_placeholder)
                tf.add_to_collection(kwargs['Model_name'] + '_Output', output)
                tf.add_to_collection(kwargs['Model_name'] + '_Dropout_prob_ph', dropout_prob_placeholder)
                tf.add_to_collection(kwargs['Model_name'] + '_State', state_placeholder)
                tf.add_to_collection(kwargs['Model_name'] + '_Loss', Weighted_BCE_loss)
                tf.add_to_collection(kwargs['Model_name'] + '_Loss', Dice_loss)
                tf.add_to_collection(kwargs['Model_name'] + '_Loss', EU_loss)
                tf.add_to_collection(kwargs['Model_name'] +'_Prior_path', prior_image_path)

                
                #Graph Summaries
                if kwargs['Summary']:
                    tf.summary.image('PI', prior_image)
                    tf.summary.image('mask', tf.reshape(Wmask, [1,kwargs['Image_width'], kwargs['Image_height'], 1]))
                    tf.summary.scalar('WBCE loss', Weighted_BCE_loss)
                    tf.summary.image('WCBE', tf.reshape(W_I, [1,kwargs['Image_width'], kwargs['Image_height'], 1]))
                return 'Segmentation'
    '''

