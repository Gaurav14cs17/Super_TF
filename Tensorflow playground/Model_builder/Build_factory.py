from utils.builder import Builder
import tensorflow as tf


class Factory(object):
    """Factory class to build DNN Architectures"""
    #Look into adding a datastructure to keep track of last layer added to the graph


    def get_model(self):
        #return self.Build_Lenet()
        print('Build_'+self.model_name+'()')
        return (eval('self.Build_'+self.model_name+'()'))


    def Build_FRRN_C(self):
        '''
        Same basic architecture as FRNN_A 
        Replaced unpooling layer with bilinear resizing 
        Added dilated convolutions to center FRRU block
        '''
        with tf.name_scope('FRRN_C'):
            with Builder(**self.kwargs) as frnn_c_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']], name='Mask')
                weight_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']], name='Weight')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                state_placeholder = tf.placeholder(tf.string, name="State")
                input_reshape = frnn_c_builder.Reshape_input(input_placeholder, \
                    width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                frnn_c_builder.control_params(Dropout_control=dropout_prob_placeholder, State=state_placeholder)

                #Construct functional building blocks
                def RU(input, filters):
                    with tf.name_scope('Residual_Unit'):
                        Conv1 = frnn_c_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv2 = frnn_c_builder.Conv2d_layer(Conv1, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv3 = frnn_c_builder.Conv2d_layer(Conv2, k_size=[1, 1], stride=[1, 1, 1, 1], filters=filters, Activation=False)

                        return frnn_c_builder.Residual_connect([input, Conv3])

                def FRRU(Residual_stream, Pooling_stream, scale_factor, filters, res_filters=32):
                    with tf.name_scope('Full_Resolution_Unit'):
                        scale_dims = [1, scale_factor, scale_factor, 1]
                        Pool, Ind = frnn_c_builder.Pool_layer(Residual_stream, k_size=scale_dims, stride=scale_dims, pooling_type='MAXIND')

                        Concat = frnn_c_builder.Concat([Pool, Pooling_stream])

                        #Conv0 = frnn_c_builder.Conv2d_layer(Concat, stride=[1,1,1,1], k_size=[1,1], filters=filters, Batch_norm=True)
                        Conv1 = frnn_c_builder.Conv2d_layer(Concat, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv2 = frnn_c_builder.Conv2d_layer(Conv1, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)

                        #Res_connect = frnn_c_builder.Residual_connect([Conv0, Conv2])
                        Conv3 = frnn_c_builder.Conv2d_layer(Conv2, k_size=[1, 1], stride=[1, 1, 1, 1], filters=res_filters, Activation=False)

                        Unpool = frnn_c_builder.Unpool_layer(Conv3, Ind, k_size = scale_dims)
                    Residual_stream_out = frnn_c_builder.Residual_connect([Residual_stream, Unpool], Activation=False)
                    Pooling_stream_out = Conv2
                    #return Conv2
                    return Residual_stream_out, Pooling_stream_out

                def Center_pool(input):
                    ''' Dense dialations '''
                    Dconv1 = frnn_c_builder.DConv_layer(input, filters=768, Batch_norm=True, D_rate=1, Activation=False)
                    Dense_connect1 = frnn_c_builder.Residual_connect([input, Dconv1])

                    Dconv2 = frnn_c_builder.DConv_layer(Dense_connect2, filters=768, Batch_norm=True, D_rate=2, Activation=False)
                    Dense_connect2 = frnn_c_builder.Residual_connect([input, Dconv1, Dconv2])

                    Dconv4 = frnn_c_builder.DConv_layer(Dense_connect3, filters=768, Batch_norm=True, D_rate=4, Activation=False)
                    Dense_connect3 = frnn_c_builder.Residual_connect([input, Dconv1, Dconv2, Dconv4 ])

                    Dconv8 = frnn_c_builder.DConv_layer(Dense_connect4, filters=768, Batch_norm=True, D_rate=8, Activation=False)
                    Dense_connect4 = frnn_c_builder.Residual_connect([input, Dconv1, Dconv2, Dconv4, Dconv8])

                    Dconv16 = frnn_c_builder.DConv_layer(Dense_connect5, filters=768, Batch_norm=True, D_rate=16, Activation=False)
                    Dense_connect5 = frnn_c_builder.Residual_connect([input, Dconv1, Dconv2, Dconv4, Dconv8, Dconv16])

                    Dconv32 = frnn_c_builder.DConv_layer(Dense_connect6, filters=768, Batch_norm=True, D_rate=32, Activation=False)
                    Dense_connect6 = frnn_c_builder.Residual_connect([input, Dconv1, Dconv2. Dconv4, Dconv8, Dconv16, Dconv32])

                    Scale_output = frnn_c_builder.Scale_activations(Dense_connect6, scale_factor=0.2)

                    return Scale_output

                #Model Construction
                Stem = frnn_c_builder.Conv2d_layer(input_reshape, stride=[1, 1, 1, 1], k_size=[5, 5], filters=48, Batch_norm=True)
                Stem = RU(Stem, 48)
                Stem_pool = frnn_c_builder.Pool_layer(Stem)
                
                Stem_pool = RU(Stem_pool, 48)
                Stem_pool = RU(Stem_pool, 48)

                Residual_stream = frnn_c_builder.Conv2d_layer(Stem_pool, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                Pooling_stream, ind1 = frnn_c_builder.Pool_layer(Stem_pool, pooling_type='MAXIND')

                #Encoder
                scale_factor = 2
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)

                Pooling_stream, ind2 = frnn_c_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor = 4
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                Pooling_stream, ind3 = frnn_c_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=8
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                Pooling_stream, ind4 = frnn_c_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=16
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)

                Pooling_stream, ind5 = frnn_c_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=32
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                Pooling_stream, ind6 = frnn_c_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=64
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                #Decoder
                Pooling_stream = frnn_c_builder.Unpool_layer(Pooling_stream, ind6)
                scale_factor = 32
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                Pooling_stream = frnn_c_builder.Unpool_layer(Pooling_stream, ind5)
                scale_factor = 16
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)


                Pooling_stream = frnn_c_builder.Unpool_layer(Pooling_stream, ind4)

                scale_factor = 8
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                
                Pooling_stream = frnn_c_builder.Unpool_layer(Pooling_stream, ind3)

                scale_factor = 4
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                Pooling_stream = frnn_c_builder.Conv2d_layer(Pooling_stream, stride=[1, 1, 1, 1], k_size=[1, 1], filters=96, Batch_norm=True)
                Pooling_stream = frnn_c_builder.Unpool_layer(Pooling_stream, ind2)

                scale_factor = 2
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)

                Pooling_stream = frnn_c_builder.Conv2d_layer(Pooling_stream, stride=[1, 1, 1, 1], k_size=[1, 1], filters=48, Batch_norm=True)
                Pooling_stream = frnn_c_builder.Unpool_layer(Pooling_stream, ind1)

                RP_stream_merge = frnn_c_builder.Concat([Pooling_stream, Residual_stream])
                Conv3 = frnn_c_builder.Conv2d_layer(RP_stream_merge, stride=[1, 1, 1, 1], k_size=[1, 1], filters=48, Batch_norm=True)
                
                Conv3 = RU(Conv3, 48)
                Conv3 = RU(Conv3, 48)


                
                Upconv = frnn_c_builder.Upconv_layer(Conv3, stride=[1, 2, 2, 1], filters=48, Batch_norm=True, output_shape=[self.kwargs['Image_width'], self.kwargs['Image_height']])
                Res_connect = frnn_c_builder.Residual_connect([Stem, Upconv])
                Res_connect = RU(Res_connect, 48)
                output = frnn_c_builder.Conv2d_layer(Res_connect, filters=1, stride=[1, 1, 1, 1], k_size=[1, 1], Batch_norm=True, Activation=False)

                #Add loss and debug
                with tf.name_scope('BCE_Loss'):
                    weights = tf.reshape(weight_placeholder, shape=[-1, self.kwargs['Image_width']*self.kwargs['Image_height']])
                    w2 = weights
                    print(self.kwargs['Image_width']*self.kwargs['Image_height'])
                    logits = tf.reshape(output, shape= [-1, self.kwargs['Image_width']*self.kwargs['Image_height']])
                    P = tf.minimum(tf.nn.sigmoid(logits)+1e-4,1.0) #safe for log sigmoid
                    F1= -output_placeholder*tf.pow(1-P,2)*tf.log(P) -(1-output_placeholder)*tf.pow(P,2)*tf.log(1-P+1e-4)
                    tf.summary.image('FOCAL Loss', tf.reshape(F1,[1, 1024, 1024, 1]))
                    F1_count = tf.count_nonzero(tf.maximum(F1-0.1,0))
                    final_focal_loss = tf.multiply(tf.reduce_sum(F1)/ tf.to_float(F1_count), 0.5)
                    tf.summary.scalar('Count focal loss', F1_count)
                    tf.summary.scalar('Focal losssum ', tf.reduce_sum(F1))
                    #focal_loss = tf.multiply(tf.multiply(Y, tf.square(1 - P)),L) + tf.multiply(tf.multiply(1-Y, tf.square(P)),max_x+L)
                    #final_focal_loss = tf.reduce_mean(focal_loss)
                    #eps = tf.constant(value=1e-5)
                    #sigmoid = tf.nn.sigmoid(logits) + eps
                    W_I = tf.multiply(tf.nn.sigmoid_cross_entropy_with_logits(logits=logits, labels=output_placeholder),1)
                    tf.summary.image('WCBE', tf.reshape(W_I, [1, 1024, 1024, 1]))
                    W_I_count = tf.count_nonzero(tf.maximum(W_I-0.1,0))
                    W_Is = tf.reduce_sum(W_I) / tf.to_float(W_I_count)
                    Weighted_BCE_loss = tf.multiply(W_Is,0.5) #0.8
                    tf.summary.scalar('Count WCBE loss', W_I_count)
                    tf.summary.scalar('WCBE losssum ', tf.reduce_sum(W_I))
                    #Weighted_BCE_loss = tf.reduce_mean(output_placeholder * tf.log(sigmoid)) #Fix output and weight shape
                    #Weighted_BCE_loss = tf.multiply(BCE_loss, weight_placeholder) + tf.multiply(tf.clip_by_value(logits, 0, 1e4), weight_placeholder)
                    #Weighted_BCE_loss = tf.reduce_mean(Weighted_BCE_loss)

                #Dice Loss
                
                with tf.name_scope('Dice_Loss'):

                    eps = tf.constant(value=1e-5, name='eps')
                    sigmoid = tf.nn.sigmoid(logits,name='sigmoid') + eps
                    intersection =tf.reduce_sum(sigmoid * output_placeholder,axis=1,name='intersection')
                    union = tf.reduce_sum(sigmoid,1,name='reduce_sigmoid') + tf.reduce_sum(output_placeholder,1,name='reduce_mask') + 1e-5
                    Dice_loss = 2 * intersection / (union)
                    Dice_loss = 1 - tf.reduce_mean(Dice_loss,name='diceloss')
                    frnn_c_builder.variable_summaries(sigmoid, name='logits')
                
                #Graph Exports
                tf.add_to_collection(self.model_name + '_Input_ph', input_placeholder)
                tf.add_to_collection(self.model_name + '_Input_reshape', input_reshape)
                tf.add_to_collection(self.model_name + '_Weight_ph', weight_placeholder)
                tf.add_to_collection(self.model_name + '_Output_ph', output_placeholder)
                tf.add_to_collection(self.model_name + '_Output', output)
                tf.add_to_collection(self.model_name + '_Dropout_prob_ph', dropout_prob_placeholder)
                tf.add_to_collection(self.model_name + '_State', state_placeholder)
                tf.add_to_collection(self.model_name + '_Loss', Weighted_BCE_loss)
                tf.add_to_collection(self.model_name + '_Loss', Dice_loss)
                tf.add_to_collection(self.model_name + '_Loss', final_focal_loss)
                tf.summary.scalar('WBCE loss', Weighted_BCE_loss)
                tf.summary.scalar('Dice loss', Dice_loss)
                tf.summary.scalar('Focal loss', final_focal_loss)
                return 'Segmentation'

    def Build_FRRN_A(self):
        with tf.name_scope('FRRN_A'):
            with Builder(**self.kwargs) as frnn_a_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']], name='Mask')
                weight_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']], name='Weight')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                state_placeholder = tf.placeholder(tf.string, name="State")
                input_reshape = frnn_a_builder.Reshape_input(input_placeholder, \
                    width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                frnn_a_builder.control_params(Dropout_control=dropout_prob_placeholder, State=state_placeholder)

                #Construct functional building blocks
                def RU(input, filters):
                    with tf.name_scope('Residual_Unit'):
                        Conv1 = frnn_a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv2 = frnn_a_builder.Conv2d_layer(Conv1, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv3 = frnn_a_builder.Conv2d_layer(Conv2, k_size=[1, 1], stride=[1, 1, 1, 1], filters=filters, Activation=False)

                        return frnn_a_builder.Residual_connect([input, Conv3])

                def FRRU(Residual_stream, Pooling_stream, scale_factor, filters, res_filters=32):
                    with tf.name_scope('Full_Resolution_Unit'):
                        scale_dims = [1, scale_factor, scale_factor, 1]
                        Pool, Ind = frnn_a_builder.Pool_layer(Residual_stream, k_size=scale_dims, stride=scale_dims, pooling_type='MAXIND')

                        Concat = frnn_a_builder.Concat([Pool, Pooling_stream])

                        #Conv0 = frnn_a_builder.Conv2d_layer(Concat, stride=[1,1,1,1], k_size=[1,1], filters=filters, Batch_norm=True)
                        Conv1 = frnn_a_builder.Conv2d_layer(Concat, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)
                        Conv2 = frnn_a_builder.Conv2d_layer(Conv1, stride=[1, 1, 1, 1], filters=filters, Batch_norm=True)

                        #Res_connect = frnn_a_builder.Residual_connect([Conv0, Conv2])
                        Conv3 = frnn_a_builder.Conv2d_layer(Conv2, k_size=[1, 1], stride=[1, 1, 1, 1], filters=res_filters, Activation=False)

                        Unpool = frnn_a_builder.Unpool_layer(Conv3, Ind, k_size = scale_dims)
                    Residual_stream_out = frnn_a_builder.Residual_connect([Residual_stream, Unpool])
                    Pooling_stream_out = Conv2

                    return Residual_stream_out, Pooling_stream_out
                    #return Conv2

                #Model Construction
                Stem = frnn_a_builder.Conv2d_layer(input_reshape, stride=[1, 1, 1, 1], k_size=[5, 5], filters=48, Batch_norm=True)
                Stem = RU(Stem, 48)
                Stem_pool = frnn_a_builder.Pool_layer(Stem)
                
                Stem_pool = RU(Stem_pool, 48)
                Stem_pool = RU(Stem_pool, 48)

                Residual_stream = frnn_a_builder.Conv2d_layer(Stem_pool, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                Pooling_stream, ind1 = frnn_a_builder.Pool_layer(Stem_pool, pooling_type='MAXIND')

                #Encoder
                scale_factor = 2
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)

                Pooling_stream, ind2 = frnn_a_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor = 4
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                Pooling_stream, ind3 = frnn_a_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=8
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                Pooling_stream, ind4 = frnn_a_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=16
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)

                Pooling_stream, ind5 = frnn_a_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=32
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                Pooling_stream, ind6 = frnn_a_builder.Pool_layer(Pooling_stream, pooling_type='MAXIND')

                scale_factor=64
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                #Decoder
                Pooling_stream = frnn_a_builder.Unpool_layer(Pooling_stream, ind6)
                scale_factor = 32
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=384)
                Pooling_stream = frnn_a_builder.Unpool_layer(Pooling_stream, ind5)
                scale_factor = 16
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)


                Pooling_stream = frnn_a_builder.Unpool_layer(Pooling_stream, ind4)

                scale_factor = 8
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                
                Pooling_stream = frnn_a_builder.Unpool_layer(Pooling_stream, ind3)

                scale_factor = 4
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=192)

                Pooling_stream = frnn_a_builder.Conv2d_layer(Pooling_stream, stride=[1, 1, 1, 1], k_size=[1, 1], filters=96, Batch_norm=True)
                Pooling_stream = frnn_a_builder.Unpool_layer(Pooling_stream, ind2)

                scale_factor = 2
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)
                Residual_stream, Pooling_stream = FRRU(Residual_stream=Residual_stream, Pooling_stream=Pooling_stream, scale_factor=scale_factor, filters=96)

                Pooling_stream = frnn_a_builder.Conv2d_layer(Pooling_stream, stride=[1, 1, 1, 1], k_size=[1, 1], filters=48, Batch_norm=True)
                Pooling_stream = frnn_a_builder.Unpool_layer(Pooling_stream, ind1)

                RP_stream_merge = frnn_a_builder.Concat([Pooling_stream, Residual_stream])
                Conv3 = frnn_a_builder.Conv2d_layer(RP_stream_merge, stride=[1, 1, 1, 1], k_size=[1, 1], filters=48, Batch_norm=True)
                
                Conv3 = RU(Conv3, 48)
                Conv3 = RU(Conv3, 48)


                
                Upconv = frnn_a_builder.Upconv_layer(Conv3, stride=[1, 2, 2, 1], filters=48, Batch_norm=True, output_shape=[self.kwargs['Image_width'], self.kwargs['Image_height']])
                Res_connect = frnn_a_builder.Residual_connect([Stem, Upconv])
                Res_connect = RU(Res_connect, 48)
                output = frnn_a_builder.Conv2d_layer(Res_connect, filters=1, stride=[1, 1, 1, 1], k_size=[1, 1], Batch_norm=True, Activation=False)

                #Add loss and debug
                with tf.name_scope('BCE_Loss'):
                    weights = tf.reshape(weight_placeholder, shape=[-1, self.kwargs['Image_width']*self.kwargs['Image_height']])
                    w2 = weights
                    print(self.kwargs['Image_width']*self.kwargs['Image_height'])
                    logits = tf.reshape(output, shape= [-1, self.kwargs['Image_width']*self.kwargs['Image_height']])
                    P = tf.minimum(tf.nn.sigmoid(logits)+1e-4,1.0) #safe for log sigmoid
                    F1= -output_placeholder*tf.pow(1-P,2)*tf.log(P) -(1-output_placeholder)*tf.pow(P,2)*tf.log(1-P+1e-4)
                    tf.summary.image('FOCAL Loss', tf.reshape(F1,[1, 1024, 1024, 1]))
                    F1_count = tf.count_nonzero(tf.maximum(F1-0.1,0))
                    final_focal_loss = tf.multiply(tf.reduce_sum(F1)/ tf.to_float(F1_count), 0.5)
                    tf.summary.scalar('Count focal loss', F1_count)
                    tf.summary.scalar('Focal losssum ', tf.reduce_sum(F1))
                    #focal_loss = tf.multiply(tf.multiply(Y, tf.square(1 - P)),L) + tf.multiply(tf.multiply(1-Y, tf.square(P)),max_x+L)
                    #final_focal_loss = tf.reduce_mean(focal_loss)
                    #eps = tf.constant(value=1e-5)
                    #sigmoid = tf.nn.sigmoid(logits) + eps
                    W_I = tf.multiply(tf.nn.sigmoid_cross_entropy_with_logits(logits=logits, labels=output_placeholder),1)
                    tf.summary.image('WCBE', tf.reshape(W_I, [1, 1024, 1024, 1]))
                    W_I_count = tf.count_nonzero(tf.maximum(W_I-0.1,0))
                    W_Is = tf.reduce_sum(W_I) / tf.to_float(W_I_count)
                    Weighted_BCE_loss = tf.multiply(W_Is,0.5) #0.8
                    tf.summary.scalar('Count WCBE loss', W_I_count)
                    tf.summary.scalar('WCBE losssum ', tf.reduce_sum(W_I))
                    #Weighted_BCE_loss = tf.reduce_mean(output_placeholder * tf.log(sigmoid)) #Fix output and weight shape
                    #Weighted_BCE_loss = tf.multiply(BCE_loss, weight_placeholder) + tf.multiply(tf.clip_by_value(logits, 0, 1e4), weight_placeholder)
                    #Weighted_BCE_loss = tf.reduce_mean(Weighted_BCE_loss)

                #Dice Loss
                
                with tf.name_scope('Dice_Loss'):

                    eps = tf.constant(value=1e-5, name='eps')
                    sigmoid = tf.nn.sigmoid(logits,name='sigmoid') + eps
                    intersection =tf.reduce_sum(sigmoid * output_placeholder,axis=1,name='intersection')
                    union = tf.reduce_sum(sigmoid,1,name='reduce_sigmoid') + tf.reduce_sum(output_placeholder,1,name='reduce_mask') + 1e-5
                    Dice_loss = 2 * intersection / (union)
                    Dice_loss = 1 - tf.reduce_mean(Dice_loss,name='diceloss')
                    frnn_a_builder.variable_summaries(sigmoid, name='logits')
                
                #Graph Exports
                tf.add_to_collection(self.model_name + '_Input_ph', input_placeholder)
                tf.add_to_collection(self.model_name + '_Input_reshape', input_reshape)
                tf.add_to_collection(self.model_name + '_Weight_ph', weight_placeholder)
                tf.add_to_collection(self.model_name + '_Output_ph', output_placeholder)
                tf.add_to_collection(self.model_name + '_Output', output)
                tf.add_to_collection(self.model_name + '_Dropout_prob_ph', dropout_prob_placeholder)
                tf.add_to_collection(self.model_name + '_State', state_placeholder)
                tf.add_to_collection(self.model_name + '_Loss', Weighted_BCE_loss)
                tf.add_to_collection(self.model_name + '_Loss', Dice_loss)
                tf.add_to_collection(self.model_name + '_Loss', final_focal_loss)
                tf.summary.scalar('WBCE loss', Weighted_BCE_loss)
                tf.summary.scalar('Dice loss', Dice_loss)
                tf.summary.scalar('Focal loss', final_focal_loss)
                return 'Segmentation'

    def Build_Unet_resnet(self):
        with tf.name_scope('Unet_resnet'):
            with Builder(**self.kwargs) as unet_res_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']], name='Mask')
                weight_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']], name='Weight')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                state_placeholder = tf.placeholder(tf.string, name="State")
                input_reshape = unet_res_builder.Reshape_input(input_placeholder, \
                    width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])
                #batch_size = tf.slice(tf.shape(input_placeholder),[0],[1])
                #Setting control params
                unet_res_builder.control_params(Dropout_control=dropout_prob_placeholder, State=state_placeholder)

                def stack_encoder(input, out_filters):
                    with tf.name_scope('Encoder'):
                        input = unet_res_builder.Relu(input)

                        #conv1a_split1 = unet_res_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=out_filters, Activation=False, Batch_norm=True)

                        conv1 = unet_res_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Batch_norm=True)
                        conv2 = unet_res_builder.Conv2d_layer(conv1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Batch_norm=True)

                        #res_connect = unet_res_builder.Residual_connect([conv1a_split1, conv2b_split1])

                        return conv2
                def stack_decoder(input, encoder_connect, out_filters, output_shape, infilter=None):
                    with tf.name_scope('Decoder'):
                        encoder_connect_shape = encoder_connect.get_shape().as_list()
                        del encoder_connect_shape[0]
                        res_filters = encoder_connect_shape.pop(2)

                        if infilter is not None:
                            res_filters=infilter
                        upscale_input = unet_res_builder.Upconv_layer(input, stride=[1, 2, 2, 1], filters=res_filters, Batch_norm=True, output_shape=output_shape) #change_filters to match encoder_connect filters
                        uconnect = unet_res_builder.Concat([encoder_connect, upscale_input])
                        conv1 = unet_res_builder.Conv2d_layer(uconnect, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Batch_norm=True)
                        conv2 = unet_res_builder.Conv2d_layer(conv1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Batch_norm=True)
                        conv3 = unet_res_builder.Conv2d_layer(conv2, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Batch_norm=True)
                        return conv3
                        '''
                        u_connect = unet_res_builder.Concat([encoder_connect, upscale_input])
                        conv1 = unet_res_builder.Conv2d_layer(u_connect, stride=[1, 1, 1, 1], k_size=[1, 1], filters=out_filters, Batch_norm=True)


                        conv1a_split1 = unet_res_builder.Conv2d_layer(conv1, stride=[1, 1, 1, 1], k_size=[1, 1], filters=out_filters, Activation=False, Batch_norm=True)

                        conv1b_split1 = unet_res_builder.Conv2d_layer(conv1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Batch_norm=True)
                        conv2b_split1 = unet_res_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=out_filters, Activation=False, Batch_norm=True)

                        res_connect = unet_res_builder.Residual_connect([conv1a_split1, conv2b_split1])

                        return res_connect
                        '''

                #Build Encoder
                
                Encoder1 = stack_encoder(input_reshape, 24)
                Pool1 = unet_res_builder.Pool_layer(Encoder1) #512

                Encoder2 = stack_encoder(Pool1, 64)
                Pool2 = unet_res_builder.Pool_layer(Encoder2) #256

                Encoder3 = stack_encoder(Pool2, 128)
                Pool3 = unet_res_builder.Pool_layer(Encoder3) #128

                Encoder4 = stack_encoder(Pool3, 256)
                Pool4 = unet_res_builder.Pool_layer(Encoder4) #64

                Encoder5 = stack_encoder(Pool4, 512)
                Pool5 = unet_res_builder.Pool_layer(Encoder5) #32

                Encoder6 = stack_encoder(Pool5, 768)
                Pool6 = unet_res_builder.Pool_layer(Encoder6) #16

                Encoder7 = stack_encoder(Pool6, 768)
                Pool7 = unet_res_builder.Pool_layer(Encoder7) #8

                #Center
                Conv_center = unet_res_builder.Conv2d_layer(Pool7, stride=[1, 1, 1, 1], filters=768, Batch_norm=True, padding='SAME')
                #Pool_center = unet_res_builder.Pool_layer(Conv_center) #8
                #Build Decoder
                Decode1 = stack_decoder(Conv_center, Encoder7, out_filters=768, output_shape=[16, 16])
                Decode2 = stack_decoder(Decode1, Encoder6, out_filters=768, output_shape=[32, 32])
                Decode3 = stack_decoder(Decode2, Encoder5, out_filters=512, output_shape=[64, 64], infilter=768)
                Decode4 = stack_decoder(Decode3, Encoder4, out_filters=256, output_shape=[128, 128], infilter=512)
                Decode5 = stack_decoder(Decode4, Encoder3, out_filters=128, output_shape=[256, 256], infilter=256)
                Decode6 = stack_decoder(Decode5, Encoder2, out_filters=64, output_shape=[512,512],  infilter=128)
                Decode7 = stack_decoder(Decode6, Encoder1, out_filters=24, output_shape=[1024,1024], infilter=64)

                output = unet_res_builder.Conv2d_layer(Decode7, stride=[1, 1, 1, 1], filters=1, Batch_norm=True, k_size=[1, 1], Activation=False) #output
                
                '''
                Encoder1 = stack_encoder(input_reshape, 128)
                Pool1 = unet_res_builder.Pool_layer(Encoder1) #64

                Encoder2 = stack_encoder(Pool1, 256)
                Pool2 = unet_res_builder.Pool_layer(Encoder2) #32

                Encoder3 = stack_encoder(Pool2, 512)
                Pool3 = unet_res_builder.Pool_layer(Encoder3) #16

                Encoder4 = stack_encoder(Pool3, 1024)
                Pool4 = unet_res_builder.Pool_layer(Encoder4) #8

                Conv_center = unet_res_builder.Conv2d_layer(Pool4, stride=[1, 1, 1, 1], filters=1024, Batch_norm=True, padding='SAME')

                Decode1 = stack_decoder(Conv_center, Encoder4, out_filters=512, output_shape=[16, 16])
                Decode2 = stack_decoder(Decode1, Encoder3, out_filters=256, output_shape=[32, 32])
                Decode3 = stack_decoder(Decode2, Encoder2, out_filters=128, output_shape=[64, 64])
                Decode4 = stack_decoder(Decode3, Encoder1, out_filters=64, output_shape=[128, 128])

                output = unet_res_builder.Conv2d_layer(Decode4, stride=[1, 1, 1, 1], filters=1, Batch_norm=True, k_size=[1, 1]) #output
                unet_res_builder.variable_summaries(output, name='output')
                unet_res_builder.variable_summaries(input_placeholder, name='input')
                '''
                #Add loss and debug
                with tf.name_scope('BCE_Loss'):
                    weights = tf.reshape(weight_placeholder, shape=[-1, self.kwargs['Image_width']*self.kwargs['Image_height']])
                    w2 = weights
                    print(self.kwargs['Image_width']*self.kwargs['Image_height'])
                    logits = tf.reshape(output, shape= [-1, self.kwargs['Image_width']*self.kwargs['Image_height']])
                    x = tf.abs(logits)
                    max_x = tf.maximum(logits,0)
                    L = tf.log(1+ tf.exp(-x))
                    Y= output_placeholder
                    P = tf.nn.sigmoid(x)
                    #focal_loss = tf.multiply(tf.multiply(tf.multiply(Y, tf.square(1 - P)),L) + tf.multiply(tf.multiply(1-Y, tf.square(P)),max_x+L),w2)
                    Weighted_BCE_loss = tf.multiply(tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=logits, labels=output_placeholder)),0.6) #0.8
                    focal_loss = tf.multiply(tf.multiply(Y, tf.square(1 - P)),L) + tf.multiply(tf.multiply(1-Y, tf.square(P)),max_x+L)
                    final_focal_loss = tf.reduce_mean(focal_loss)

                #Dice Loss
                
                with tf.name_scope('Dice_Loss'):
                    eps = tf.constant(value=1e-5, name='eps')
                    sigmoid = tf.nn.sigmoid(logits,name='sigmoid') + eps
                    #intersection =tf.reduce_sum(sigmoid * output_placeholder*w2,axis=1,name='intersection') + 1
                    intersection =tf.reduce_sum(sigmoid * output_placeholder,axis=1,name='intersection') + 1
                    #union = eps + tf.reduce_sum(sigmoid*w2,1,name='reduce_sigmoid') + (tf.reduce_sum(output_placeholder*w2,1,name='reduce_mask') + 1)
                    union = eps + tf.reduce_sum(sigmoid,1,name='reduce_sigmoid') + (tf.reduce_sum(output_placeholder,1,name='reduce_mask') + 1)
                    Dice_loss = 2 * intersection / (union)
                    Dice_loss = 1 - tf.reduce_mean(Dice_loss,name='diceloss')
                    unet_res_builder.variable_summaries(sigmoid, name='logits')
                
                #Graph Exports
                tf.add_to_collection(self.model_name + '_Input_ph', input_placeholder)
                tf.add_to_collection(self.model_name + '_Input_reshape', input_reshape)
                tf.add_to_collection(self.model_name + '_Weight_ph', weight_placeholder)
                tf.add_to_collection(self.model_name + '_Output_ph', output_placeholder)
                tf.add_to_collection(self.model_name + '_Output', output)
                tf.add_to_collection(self.model_name + '_Dropout_prob_ph', dropout_prob_placeholder)
                tf.add_to_collection(self.model_name + '_State', state_placeholder)
                tf.add_to_collection(self.model_name + '_Loss', Weighted_BCE_loss)
                tf.add_to_collection(self.model_name + '_Loss', Dice_loss)
                #tf.add_to_collection(self.model_name + '_Loss', final_focal_loss)
                return 'Segmentation'

    def Build_Inception_Resnet_v2a(self):
        with tf.name_scope('Inception_Resnet_v2a_model'):
            with Builder(**self.kwargs) as inceprv2a_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, shape=[None, self.kwargs['Classes']], name='Output')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                state_placeholder = tf.placeholder(tf.string, name="State")
                input_reshape = inceprv2a_builder.Reshape_input(input_placeholder, width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                inceprv2a_builder.control_params(Dropout_control=dropout_prob_placeholder, State=state_placeholder)

                #Construct functional building blocks
                def stem(input):
                    with tf.name_scope('Stem'):
                        conv1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 2, 2, 1], filters=32, Batch_norm=True)
                        conv2 = inceprv2a_builder.Conv2d_layer(conv1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=32, Batch_norm=True, padding='VALID')
                        conv3 = inceprv2a_builder.Conv2d_layer(conv2, stride=[1, 1, 1, 1], k_size=[3, 3], filters=64, Batch_norm=True)
                        pool1 = inceprv2a_builder.Pool_layer(conv3, stride=[1, 2, 2, 1], k_size=[1, 3 ,3, 1], padding='VALID')

                        conv4 = inceprv2a_builder.Conv2d_layer(pool1, stride=[1, 1, 1, 1], filters=80, Batch_norm=True)
                        conv5 = inceprv2a_builder.Conv2d_layer(conv4, stride=[1, 1, 1, 1], k_size=[3, 3], filters=192, Batch_norm=True, padding='VALID')

                        pool2 = inceprv2a_builder.Pool_layer(conv5, stride=[1, 2, 2, 1], k_size=[1, 3 ,3, 1], padding='VALID')

                        conv1a_split1 = inceprv2a_builder.Conv2d_layer(pool2, stride=[1, 1, 1, 1], filters=96, Batch_norm=True)

                        conv1b_split1 = inceprv2a_builder.Conv2d_layer(pool2, stride=[1, 1, 1, 1], filters=48, Batch_norm=True)
                        conv2b_split1 = inceprv2a_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], k_size=[5, 5], filters=64, Batch_norm=True)

                        conv1c_split1 = inceprv2a_builder.Conv2d_layer(pool2, stride=[1, 1, 1, 1], filters=64, Batch_norm=True)
                        conv2c_split1 = inceprv2a_builder.Conv2d_layer(conv1c_split1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=96, Batch_norm=True)
                        conv3c_split1 = inceprv2a_builder.Conv2d_layer(conv2c_split1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=96, Batch_norm=True)

                        avgpool1d_split1 = inceprv2a_builder.Pool_layer(pool2, k_size=[1, 3, 3, 1], stride=[1, 1, 1, 1], pooling_type='AVG')
                        conv1d_split1 = inceprv2a_builder.Conv2d_layer(avgpool1d_split1, k_size=[1, 1], filters=64, Batch_norm=True)

                        concat = inceprv2a_builder.Concat([conv1a_split1, conv2b_split1, conv3c_split1, conv1d_split1])

                        return concat

                def incep_block35(input, Activation=True, scale=1.0):
                    with tf.name_scope('Block35'):
                        conv1a_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)

                        conv1b_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                        conv2b_split1 = inceprv2a_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], filters=32, Batch_norm=True)

                        conv1c_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                        conv2c_split1 = inceprv2a_builder.Conv2d_layer(conv1c_split1, stride=[1, 1, 1, 1], filters=48, Batch_norm=True)
                        conv3c_split1 = inceprv2a_builder.Conv2d_layer(conv2c_split1, stride=[1, 1, 1, 1], filters=64, Batch_norm=True)

                        concat = inceprv2a_builder.Concat([conv1a_split1, conv2b_split1, conv3c_split1])

                        conv2 = inceprv2a_builder.Conv2d_layer(concat, stride=[1, 1, 1, 1], k_size=[1, 1], filters=input.get_shape()[3], Batch_norm=False, Activation=False)
                        conv2_scale = inceprv2a_builder.Scale_activations(conv2,scaling_factor=scale)
                        residual_out = inceprv2a_builder.Residual_connect([input, conv2_scale], Activation=Activation)

                        return residual_out

                def incep_block17(input, Activation=True, scale=1.0):
                    with tf.name_scope('Block17'):
                        conv1a_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=192, Batch_norm=True)

                        conv1b_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=128, Batch_norm=True)
                        conv2b_split1 = inceprv2a_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], k_size=[1, 7], filters=160, Batch_norm=True)
                        conv3b_split1 = inceprv2a_builder.Conv2d_layer(conv2b_split1, stride=[1, 1, 1, 1], k_size=[7, 1], filters=192, Batch_norm=True)

                        concat = inceprv2a_builder.Concat([conv1a_split1, conv3b_split1])

                        conv2 = inceprv2a_builder.Conv2d_layer(concat, stride=[1, 1, 1, 1], k_size=[1, 1], filters=input.get_shape()[3], Batch_norm=False, Activation=False)
                        conv2_scale = inceprv2a_builder.Scale_activations(conv2,scaling_factor=scale)
                        residual_out = inceprv2a_builder.Residual_connect([input, conv2_scale], Activation=Activation)

                        return residual_out

                def incep_block8(input, Activation=True, scale=1.0):
                    with tf.name_scope('Block8'):
                        conv1a_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=192, Batch_norm=True)

                        conv1b_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=192, Batch_norm=True)
                        conv2b_split1 = inceprv2a_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], k_size=[1, 3], filters=224, Batch_norm=True)
                        conv3b_split1 = inceprv2a_builder.Conv2d_layer(conv2b_split1, stride=[1, 1, 1, 1], k_size=[3, 1], filters=256, Batch_norm=True)

                        concat = inceprv2a_builder.Concat([conv1a_split1, conv3b_split1])

                        conv2 = inceprv2a_builder.Conv2d_layer(concat, stride=[1, 1, 1, 1], k_size=[1, 1], filters=input.get_shape()[3], Batch_norm=False, Activation=False)
                        conv2_scale = inceprv2a_builder.Scale_activations(conv2,scaling_factor=scale) #Last layer has no activations, recheck with implementation
                        residual_out = inceprv2a_builder.Residual_connect([input, conv2_scale], Activation=Activation)

                        return residual_out

                def ReductionA(input):
                    with tf.name_scope('Reduction_35x17'):
                        conv1a_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 2, 2, 1], k_size=[3, 3], filters=384, Batch_norm=True, padding='VALID')

                        conv1b_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2b_split1 = inceprv2a_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=256, Batch_norm=True)
                        conv3b_split1 = inceprv2a_builder.Conv2d_layer(conv2b_split1, stride=[1, 2, 2, 1], k_size=[3, 3], filters=384, Batch_norm=True, padding='VALID')

                        pool1c_split1 = inceprv2a_builder.Pool_layer(input, stride=[1, 2, 2, 1], k_size=[1, 3, 3, 1], padding='VALID')

                        concat = inceprv2a_builder.Concat([conv1a_split1, conv3b_split1, pool1c_split1])
                        
                        return concat
                def ReductionB(input):
                    with tf.name_scope('Reduction_17x8'):
                        conv1a_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2a_split1 = inceprv2a_builder.Conv2d_layer(conv1a_split1, stride=[1, 2, 2, 1], k_size=[3, 3], filters=384, Batch_norm=True, padding='VALID')

                        conv1b_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2b_split1 = inceprv2a_builder.Conv2d_layer(conv1b_split1, stride=[1, 2, 2, 1], k_size=[3, 3], filters=288, Batch_norm=True, padding='VALID')

                        conv1c_split1 = inceprv2a_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2c_split1 = inceprv2a_builder.Conv2d_layer(conv1c_split1, stride=[1, 1, 1, 1], k_size=[3, 3], filters=288, Batch_norm=True)
                        conv3c_split1 = inceprv2a_builder.Conv2d_layer(conv2c_split1, stride=[1, 2, 2, 1], k_size=[3, 3], filters=320, Batch_norm=True, padding='VALID')

                        pool1d_split1 = inceprv2a_builder.Pool_layer(input, stride=[1, 2, 2, 1], k_size=[1, 3, 3, 1], padding='VALID')

                        concat = inceprv2a_builder.Concat([conv2a_split1, conv2b_split1, conv3c_split1, pool1d_split1])
                        return concat

                #MODEL CONSTRUCTION

                #STEM
                Block_35 = stem(input_reshape)
                #INCEPTION 35x35
                for index in range(10):
                    Block_35 = incep_block35(Block_35, scale=0.17)
                #Reduction 35->17
                Block_17 = ReductionA(Block_35)
                #INCEPTION 17x17
                for index in range(20):
                    Block_17 = incep_block17(Block_17, scale=0.1)
                #Reduction 17->8
                Block_8 = ReductionB(Block_17)
                for index in range(9):
                    Block_8 = incep_block8(Block_8, scale=0.2)
                Block_8 = incep_block8(Block_8, False)
                #Normal Logits
                with tf.name_scope('Logits'):
                    model_conv = inceprv2a_builder.Conv2d_layer(Block_8, stride=[1, 1, 1, 1], k_size=[1, 1], filters=1536, Batch_norm=True)
                    model_avg_pool = inceprv2a_builder.Pool_layer(model_conv, k_size=[1, 8, 8, 1], stride=[1, 8, 8, 1], padding='SAME', pooling_type='AVG')
                    drop1 = inceprv2a_builder.Dropout_layer(model_avg_pool)
                    output = inceprv2a_builder.FC_layer(drop1, filters=self.kwargs['Classes'], readout=True)
                #AuxLogits
                with tf.name_scope('Auxlogits'):
                    model_aux_avg_pool = inceprv2a_builder.Pool_layer(Block_17, k_size=[1, 5, 5, 1], stride=[1, 3, 3, 1], padding='VALID', pooling_type='AVG')
                    model_aux_conv1 = inceprv2a_builder.Conv2d_layer(model_aux_avg_pool, k_size=[1, 1], stride=[1, 1, 1, 1], filters=128, Batch_norm=True)
                    model_aux_conv2 = inceprv2a_builder.Conv2d_layer(model_aux_conv1, k_size=[5, 5], stride=[1, 1, 1, 1], padding='VALID', filters=768, Batch_norm=True)
                    model_aux_logits = inceprv2a_builder.FC_layer(model_aux_conv2, filters=self.kwargs['Classes'], readout=True)

                #Logit Loss
                with tf.name_scope('Cross_entropy_loss'):
                    softmax_logit_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=output_placeholder, logits=output))

                #AuxLogit Loss
                with tf.name_scope('Cross_entropy_loss'):
                    softmax_auxlogit_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=output_placeholder, logits=model_aux_logits)) * 0.6

                #Adding collections to graph
                tf.add_to_collection(self.model_name + '_Endpoints', Block_35)
                tf.add_to_collection(self.model_name + '_Endpoints', Block_17)
                tf.add_to_collection(self.model_name + '_Endpoints', Block_8)
                tf.add_to_collection(self.model_name + '_Input_ph', input_placeholder)
                tf.add_to_collection(self.model_name + '_Input_reshape', input_reshape)
                tf.add_to_collection(self.model_name + '_Output_ph', output_placeholder)
                tf.add_to_collection(self.model_name + '_Output', output)
                tf.add_to_collection(self.model_name + '_Dropout_prob_ph', dropout_prob_placeholder)
                tf.add_to_collection(self.model_name + '_State', state_placeholder)
                tf.add_to_collection(self.model_name + '_Loss', softmax_logit_loss)
                tf.add_to_collection(self.model_name + '_Loss', softmax_auxlogit_loss)


    def Build_Inception_Resnet_v2(self):
        with tf.name_scope('Inception_Resnet_v2_model'):
            with Builder(**self.kwargs) as inceprv2_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, shape=[None, self.kwargs['Classes']], name='Output')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                state_placeholder = tf.placeholder(tf.string, name="State")
                input_reshape = inceprv2_builder.Reshape_input(input_placeholder, width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                inceprv2_builder.control_params(Dropout_control=dropout_prob_placeholder, State=state_placeholder)
                
                #Construct functional building blocks
                def stem(input):
                    with tf.name_scope('Stem') as scope:
                        conv1 = inceprv2_builder.Conv2d_layer(input, stride=[1,2,2,1], filters=32, padding='VALID', Batch_norm=True)
                        conv2 = inceprv2_builder.Conv2d_layer(conv1, stride=[1,1,1,1], filters=32, padding='VALID', Batch_norm=True)
                        conv3 = inceprv2_builder.Conv2d_layer(conv2, stride=[1,1,1,1], filters=64, Batch_norm=True)
                        
                        conv1a_split1 = inceprv2_builder.Conv2d_layer(conv3, stride=[1,2,2,1], filters=96, padding='VALID', Batch_norm=True)
                        pool1b_split1 = inceprv2_builder.Pool_layer(conv3, padding='VALID')

                        concat1 = inceprv2_builder.Concat([conv1a_split1, pool1b_split1])

                        conv1a_split2 = inceprv2_builder.Conv2d_layer(concat1, stride=[1, 1, 1, 1], k_size=[1, 1], filters=64, Batch_norm=True)
                        conv2a_split2 = inceprv2_builder.Conv2d_layer(conv1a_split2, stride=[1, 1, 1, 1], k_size=[7, 1], filters=64, Batch_norm=True)
                        conv3a_split2 = inceprv2_builder.Conv2d_layer(conv2a_split2, stride=[1, 1, 1, 1], k_size=[1, 7], filters=64, Batch_norm=True)
                        conv4a_split2 = inceprv2_builder.Conv2d_layer(conv3a_split2, stride=[1, 1, 1, 1], filters=96, padding='VALID', Batch_norm=True)

                        conv1b_split2 = inceprv2_builder.Conv2d_layer(concat1, stride=[1, 1, 1, 1], k_size=[1, 1], filters=64, Batch_norm=True)
                        conv2b_split2 = inceprv2_builder.Conv2d_layer(conv1b_split2, stride=[1, 1, 1, 1], filters=96, padding='VALID', Batch_norm=True)

                        concat2 = inceprv2_builder.Concat([conv4a_split2, conv2b_split2])

                        pool1a_split3 = inceprv2_builder.Pool_layer(concat2, padding="VALID")
                        conv1b_split3 = inceprv2_builder.Conv2d_layer(concat2, stride=[1, 2, 2, 1], filters=192, padding='VALID', Batch_norm=True)

                        concat3 = inceprv2_builder.Concat([pool1a_split3, conv1b_split3])
                        return concat3

                def inception_resnet_A(input):
                    with tf.name_scope('Inception_Resnet_A') as scope:
                        conv1a_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                        conv2a_split1 = inceprv2_builder.Conv2d_layer(conv1a_split1, stride=[1, 1, 1, 1], filters=48, Batch_norm=True)
                        conv3a_split1 = inceprv2_builder.Conv2d_layer(conv2a_split1, stride=[1, 1, 1, 1], filters=64, Batch_norm=True)

                        conv1b_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                        conv2b_split1 = inceprv2_builder.Conv2d_layer(conv1b_split1, stride=[1, 1, 1, 1], filters=32, Batch_norm=True)

                        conv1c_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=32, Batch_norm=True)
                        
                        concat1 = inceprv2_builder.Concat([conv3a_split1, conv2b_split1, conv1c_split1])

                        conv2 = inceprv2_builder.Conv2d_layer(concat1, stride=[1, 1, 1, 1], k_size=[1, 1], filters=384, Batch_norm=True, Activation=False)

                        conv2_scale = inceprv2_builder.Scale_activations(conv2,scaling_factor = 1)
                        residual_out = inceprv2_builder.Residual_connect([input, conv2_scale])

                        return residual_out

                def reduction_A(input):
                    with tf.name_scope('Reduction_A') as scope:
                        '''
                        k=256, l=256, m=384, n=384
                        '''
                        conv1a_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2a_split1 = inceprv2_builder.Conv2d_layer(conv1a_split1, stride=[1, 1, 1, 1], filters=256, Batch_norm=True)
                        conv3a_split1 = inceprv2_builder.Conv2d_layer(conv2a_split1, stride=[1, 2, 2, 1], filters=384, padding='VALID', Batch_norm=True)

                        conv1b_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 2, 2, 1], filters=384, padding='VALID', Batch_norm=True)

                        pool1c_split1 = inceprv2_builder.Pool_layer(input, padding='VALID')

                        concat = inceprv2_builder.Concat([conv3a_split1, conv1b_split1, pool1c_split1])
                        
                        return concat

                def inception_resnet_B(input):
                    with tf.name_scope('Inception_Resnet_B') as scope:
                        conv1a_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=128, Batch_norm=True)
                        conv2a_split1 = inceprv2_builder.Conv2d_layer(conv1a_split1, stride=[1, 1, 1, 1], k_size=[1, 7], filters=160, Batch_norm=True)
                        conv3a_split1 = inceprv2_builder.Conv2d_layer(conv2a_split1, stride=[1, 1, 1, 1], k_size=[7, 1], filters=192, Batch_norm=True)

                        conv1b_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=192, Batch_norm=True)

                        concat1 = inceprv2_builder.Concat([conv3a_split1, conv1b_split1])

                        conv2 = inceprv2_builder.Conv2d_layer(concat1, stride=[1, 1, 1, 1], k_size=[1, 1], filters=1152, Batch_norm=True, Activation=False) #paper discrepancy filter = 1154
                        conv2_scale = inceprv2_builder.Scale_activations(conv2, scaling_factor=0.4)

                        residual_out = inceprv2_builder.Residual_connect([input, conv2_scale])

                        return residual_out

                def reduction_B(input):
                    with tf.name_scope('Reduction_B') as scope: 
                        conv1a_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2a_split1 = inceprv2_builder.Conv2d_layer(conv1a_split1, stride=[1, 1, 1, 1], filters=288, Batch_norm=True)
                        conv3a_split1 = inceprv2_builder.Conv2d_layer(conv2a_split1, stride=[1, 2, 2, 1], filters=384, padding='VALID', Batch_norm=True)

                        conv1b_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2b_split1 = inceprv2_builder.Conv2d_layer(conv1b_split1, stride=[1, 2, 2, 1], filters=256, padding='VALID', Batch_norm=True)

                        conv1c_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=256, Batch_norm=True)
                        conv2c_split1 = inceprv2_builder.Conv2d_layer(conv1c_split1, stride=[1, 2, 2, 1], filters=256, padding='VALID', Batch_norm=True)

                        pool1d_split1 = inceprv2_builder.Pool_layer(input, padding='VALID')

                        concat = inceprv2_builder.Concat([conv3a_split1, conv2b_split1, conv2c_split1, pool1d_split1])
                        return concat

                def inception_resnet_C(input):
                    with tf.name_scope('Inception_Resnet_C') as scope:
                        conv1a_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=192, Batch_norm=True)
                        conv2a_split1 = inceprv2_builder.Conv2d_layer(conv1a_split1, stride=[1, 1, 1, 1], k_size=[1, 3], filters=224, Batch_norm=True)
                        conv3a_split1 = inceprv2_builder.Conv2d_layer(conv2a_split1, stride=[1, 1, 1, 1], k_size=[3, 1], filters=256, Batch_norm=True)

                        conv1b_split1 = inceprv2_builder.Conv2d_layer(input, stride=[1, 1, 1, 1], k_size=[1, 1], filters=192, Batch_norm=True)

                        concat1 = inceprv2_builder.Concat([conv3a_split1, conv1b_split1])

                        conv2 = inceprv2_builder.Conv2d_layer(concat1, stride=[1, 1, 1, 1], k_size=[1, 1], filters=2048, Batch_norm=True, Activation=False)
                        conv2_scale = inceprv2_builder.Scale_activations(conv2)

                        residual_out = inceprv2_builder.Residual_connect([input, conv2_scale])
                        
                        return residual_out
                #MODEL CONSTRUCTION

                #STEM
                model_stem = stem(input_reshape)
                #5x INCEPTION RESNET A
                inception_A1 = inception_resnet_A(model_stem)
                inception_A2 = inception_resnet_A(inception_A1)
                inception_A3 = inception_resnet_A(inception_A2)
                inception_A4 = inception_resnet_A(inception_A3)
                inception_A5 = inception_resnet_A(inception_A4)
                #REUCTION A
                model_reduction_A = reduction_A(inception_A5)
                #10X INCEPTION RESNET B
                inception_B1 = inception_resnet_B(model_reduction_A) #Don't know if i'm missing something or now, but reduction A's output for inception resnetv2 is a tensor of depth 1152
                inception_B2 = inception_resnet_B(inception_B1)
                inception_B3 = inception_resnet_B(inception_B2)
                inception_B4 = inception_resnet_B(inception_B3)
                inception_B5 = inception_resnet_B(inception_B4)
                inception_B6 = inception_resnet_B(inception_B5)
                inception_B7 = inception_resnet_B(inception_B6)
                inception_B8 = inception_resnet_B(inception_B7)
                inception_B9 = inception_resnet_B(inception_B8)
                inception_B10 = inception_resnet_B(inception_B9)
                #REDUCTION B
                model_reduction_B = reduction_B(inception_B10)
                #5X INCEPTION RESNET C
                inception_C1 = inception_resnet_C(model_reduction_B)
                inception_C2 = inception_resnet_C(inception_C1)
                inception_C3 = inception_resnet_C(inception_C2)
                inception_C4 = inception_resnet_C(inception_C3)
                inception_C5 = inception_resnet_C(inception_C4)
                #AVERAGE POOLING
                average_pooling = inceprv2_builder.Pool_layer(inception_C5, k_size=[1, 8, 8, 1], stride=[1, 8, 8, 1], padding='SAME', pooling_type='AVG')
                #DROPOUT 
                drop1 = inceprv2_builder.Dropout_layer(average_pooling)
                #OUTPUT
                output = inceprv2_builder.FC_layer(drop1, filters=self.kwargs['Classes'], readout=True)
                #LOGIT LOSS
                with tf.name_scope('Cross_entropy_loss'):
                    softmax_logit_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=output_placeholder, logits=output))

                #Adding collections to graph
                tf.add_to_collection(self.model_name + '_Endpoints', inception_A5)
                tf.add_to_collection(self.model_name + '_Endpoints', inception_B10)
                tf.add_to_collection(self.model_name + '_Endpoints', inception_C5)
                tf.add_to_collection(self.model_name + '_Input_ph', input_placeholder)
                tf.add_to_collection(self.model_name + '_Input_reshape', input_reshape)
                tf.add_to_collection(self.model_name + '_Output_ph', output_placeholder)
                tf.add_to_collection(self.model_name + '_Output', output)
                tf.add_to_collection(self.model_name + '_Dropout_prob_ph', dropout_prob_placeholder)
                tf.add_to_collection(self.model_name + '_State', state_placeholder)
                tf.add_to_collection(self.model_name + '_Loss', softmax_logit_loss)

                #Inception_resnetv2_dict = {'Input_ph': input_placeholder, 'Output_ph': output_placeholder, 'Output': output, 'Dropout_prob_ph': dropout_prob_placeholder, 'State' : state_placeholder}
                return dropout_prob_placeholder
                #return Inception_resnetv2_dict


    def Build_vgg19(self):
        with tf.name_scope('Vgg_model'):
            with Builder(**self.kwargs) as vgg19_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, shape=[None, self.kwargs['Classes']], name='Output')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                input_reshape = vgg19_builder.Reshape_input(input_placeholder, width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                vgg19_builder.control_params(Dropout_control=dropout_prob_placeholder)

                #FEATURE EXTRACTION
                conv1a = vgg19_builder.Conv2d_layer(input_reshape, filters=64)
                conv1b = vgg19_builder.Conv2d_layer(conv1a, filters=64)

                pool1 = vgg19_builder.Pool_layer(conv1b)

                conv2a = vgg19_builder.Conv2d_layer(pool1, filters=128)
                conv2b = vgg19_builder.Conv2d_layer(conv2a, filters=128)

                pool2 = vgg19_builder.Pool_layer(conv2b)

                conv3a = vgg19_builder.Conv2d_layer(pool2, filters=256)
                conv3b = vgg19_builder.Conv2d_layer(conv3a, filters=256)
                conv3c = vgg19_builder.Conv2d_layer(conv3b, filters=256)
                conv3d = vgg19_builder.Conv2d_layer(conv3c, filters=256)

                pool3 = vgg19_builder.Pool_layer(conv3d)

                conv4a = vgg19_builder.Conv2d_layer(pool3, filters=512)
                conv4b = vgg19_builder.Conv2d_layer(conv4a, filters=512)
                conv4c = vgg19_builder.Conv2d_layer(conv4b, filters=512)
                conv4d = vgg19_builder.Conv2d_layer(conv4c, filters=512)

                pool4 = vgg19_builder.Pool_layer(conv4d)

                conv5a = vgg19_builder.Conv2d_layer(pool4, filters=512)
                conv5b = vgg19_builder.Conv2d_layer(conv5a, filters=512)
                conv5c = vgg19_builder.Conv2d_layer(conv5b, filters=512)
                conv5d = vgg19_builder.Conv2d_layer(conv5c, filters=512)

                pool5 = vgg19_builder.Pool_layer(conv5d)

                #DENSELY CONNECTED
                fc1 = vgg19_builder.FC_layer(pool5, filters=4096)
                drop1 = vgg19_builder.Dropout_layer(fc1)

                fc2 = vgg19_builder.FC_layer(drop1, filters=4096)
                drop2 = vgg19_builder.Dropout_layer(fc2)

                output = vgg19_builder.FC_layer(drop2, filters=self.kwargs['Classes'], readout=True)

                VGG19_dict = {'Input_ph': input_placeholder, 'Output_ph': output_placeholder, 'Output': output, 'Dropout_prob_ph': dropout_prob_placeholder }
                return(VGG19_dict)



    def Build_vgg16(self):
        with tf.name_scope('Vgg_model'):
            with Builder(**self.kwargs) as vgg16_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, shape=[None, self.kwargs['Classes']], name='Output')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                input_reshape = vgg16_builder.Reshape_input(input_placeholder, width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                vgg16_builder.control_params(Dropout_control=dropout_prob_placeholder)

                #FEATURE EXTRACTION
                conv1a = vgg16_builder.Conv2d_layer(input_reshape, filters=64)
                conv1b = vgg16_builder.Conv2d_layer(conv1a, filters=64)

                pool1 = vgg16_builder.Pool_layer(conv1b)

                conv2a = vgg16_builder.Conv2d_layer(pool1, filters=128)
                conv2b = vgg16_builder.Conv2d_layer(conv2a, filters=128)

                pool2 = vgg16_builder.Pool_layer(conv2b)

                conv3a = vgg16_builder.Conv2d_layer(pool2, filters=256)
                conv3b = vgg16_builder.Conv2d_layer(conv3a, filters=256)
                conv3c = vgg16_builder.Conv2d_layer(conv3b, filters=256)

                pool3 = vgg16_builder.Pool_layer(conv3c)

                conv4a = vgg16_builder.Conv2d_layer(pool3, filters=512)
                conv4b = vgg16_builder.Conv2d_layer(conv4a, filters=512)
                conv4c = vgg16_builder.Conv2d_layer(conv4b, filters=512)

                pool4 = vgg16_builder.Pool_layer(conv4c)

                conv5a = vgg16_builder.Conv2d_layer(pool4, filters=512)
                conv5b = vgg16_builder.Conv2d_layer(conv5a, filters=512)
                conv5c = vgg16_builder.Conv2d_layer(conv5b, filters=512)

                pool5 = vgg16_builder.Pool_layer(conv5c)

                #DENSELY CONNECTED
                fc1 = vgg16_builder.FC_layer(pool5, filters=4096)
                drop1 = vgg16_builder.Dropout_layer(fc1)

                fc2 = vgg16_builder.FC_layer(drop1, filters=4096)
                drop2 = vgg16_builder.Dropout_layer(fc2)

                output = vgg16_builder.FC_layer(drop2, filters=self.kwargs['Classes'], readout=True)

                VGG16_dict = {'Input_ph': input_placeholder, 'Output_ph': output_placeholder, 'Output': output, 'Dropout_prob_ph': dropout_prob_placeholder }
                return(VGG16_dict)



    def Build_Alexnet(self):
        with tf.name_scope('Alexnet_model'):
            with Builder(**self.kwargs) as alexnet_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, shape=[None, self.kwargs['Classes']], name='Output')
                dropout_prob_placeholder = tf.placeholder(tf.float32, name='Dropout')
                state_placeholder = tf.placeholder(tf.bool, name="State")

                input_reshape = alexnet_builder.Reshape_input(input_placeholder, width=self.kwargs['Image_width'], height=self.kwargs['Image_height'], colorspace= self.kwargs['Image_cspace'])

                #Setting control params
                alexnet_builder.control_params(Dropout_control=dropout_prob_placeholder, State=state_placeholder)

                #FEATURE EXTRACTION
                conv1 = alexnet_builder.Conv2d_layer(input_reshape, stride=[1, 4, 4, 1], k_size=[11, 11], filters=96, padding='VALID', Batch_norm=True)
                
                pool1 = alexnet_builder.Pool_layer(conv1, k_size=[1, 3, 3, 1], padding='VALID')

                pad1 = alexnet_builder.Pad_layer(pool1, p_type='SYMMETRIC')
                conv2 = alexnet_builder.Conv2d_layer(pad1, k_size=[5, 5], filters=256, padding='VALID', Batch_norm=True)

                pool2 = alexnet_builder.Pool_layer(conv2, k_size=[1, 3, 3, 1], padding='VALID')

                conv3 = alexnet_builder.Conv2d_layer(pool2, filters=384, Batch_norm=True)
                conv4 = alexnet_builder.Conv2d_layer(conv3, filters=384, Batch_norm=True)
                conv5 = alexnet_builder.Conv2d_layer(conv4, filters=256, Batch_norm=True)

                pool5 = alexnet_builder.Pool_layer(conv5, k_size=[1, 3, 3, 1])

                #DENSELY CONNECTED
                fc1 = alexnet_builder.FC_layer(pool5, filters=4096)
                drop1 = alexnet_builder.Dropout_layer(fc1)

                fc2 = alexnet_builder.FC_layer(drop1, filters=4096)
                drop2 = alexnet_builder.Dropout_layer(fc2)

                output = alexnet_builder.FC_layer(drop2, filters=self.kwargs['Classes'], readout=True)
                #tf.summary.image('Inputs', input_reshape)
                #tf.summary.tensor_summary('Outputs', output)
                Alexnet_dict = {'Input_ph': input_placeholder, 'Output_ph': output_placeholder, 'Output': output, 'Dropout_prob_ph': dropout_prob_placeholder, 'State' : state_placeholder}
                return(Alexnet_dict)



    def Build_Lenet(self):
        with tf.name_scope('LeNeT_Model'):
            #with Builder(Summary=True,Batch_size=50,Image_width=28,Image_height=28,Image_cspace=1) as lenet_builder:
            with Builder(**self.kwargs) as lenet_builder:
                input_placeholder = tf.placeholder(tf.float32, \
                    shape=[None, self.kwargs['Image_width']*self.kwargs['Image_height']*self.kwargs['Image_cspace']], name='Input')
                output_placeholder = tf.placeholder(tf.float32, shape=[None, self.kwargs['Classes']], name='Output')
                input_reshape = lenet_builder.Reshape_input(input_placeholder)
                
                conv1 = lenet_builder.Conv2d_layer(input_reshape, k_size=[5, 5])
                pool1 = lenet_builder.Pool_layer(conv1)

                conv2 = lenet_builder.Conv2d_layer(pool1, k_size=[5, 5], filters=64)
                pool2 = lenet_builder.Pool_layer(conv2)

                fc1 = lenet_builder.FC_layer(pool2);
                output = lenet_builder.FC_layer(fc1, filters=self.kwargs['Classes'], readout=True)

                Lenet_dict = {'Input_ph': input_placeholder, 'Output_ph': output_placeholder, 'Output': output}
                return(Lenet_dict)



    def __init__(self, **kwargs):
        #TODO: WRITE ERROR HANDLER AND PARSER 
        self.model_name = kwargs['Model_name']
        self.summary = kwargs['Summary']
        self.kwargs = kwargs
        #Add more params as required