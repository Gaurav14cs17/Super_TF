from Model_builder.Build_factory import Factory
import tensorflow as tf
import numpy as np
import cv2
class Model(object):
    """This class contains the model architecture, optimizer and loss function"""


    def __init__(self, **kwargs):
        self.Model_name = kwargs['Model_name']
        print(self.Model_name)
        self.kwargs = kwargs
        self.global_step=tf.Variable(0, trainable=False, dtype=tf.int32, name='global_step')

        #Init class dicts
        self.test_dict = {}
        self.train_dict = {}
        self.model_dict={}
        self.accuracy_op = False

    def Set_test_control(self, control_placeholders_dict):
        for key, value in control_placeholders_dict.items():
            self.test_dict[self.model_dict[key]] = value


    def Set_train_control(self, control_placeholders_dict):
        for key, value in control_placeholders_dict.items():
            self.train_dict[self.model_dict[key]] = value


    def Set_loss(self, Reg_loss=None):
        with tf.name_scope("Loss"):
            with tf.name_scope("Logit_Loss"):
                loss = tf.get_collection(self.Model_name + '_Loss') #Getting losses from the graph

            if Reg_loss is None:
                with tf.name_scope("Regularization_Loss"):
                    regularization_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
                    regularization_loss = tf.add_n(regularization_losses, name='regularization_loss')
                    loss.append(regularization_loss)
            
            self.loss = tf.add_n(loss)
            if self.kwargs['Summary']:
                tf.summary.scalar('Total', self.loss)


    def Set_optimizer(self, starter_learning_rate=0.0001, decay_steps=100000, decay_rate=0.84, Fixed_LR=None, Optimizer='RMS', Optimizer_params=None, Gradient_norm=None): #0.0001
        #TODO: CHANGE TO OPTIMIZER FACTORY

        if Fixed_LR is None:
            learning_rate = tf.train.exponential_decay(starter_learning_rate, self.global_step, decay_steps=decay_steps, decay_rate=decay_rate, staircase=True)
        else:
            learning_rate = starter_learning_rate
        if self.kwargs['Summary']:
            tf.summary.scalar('Learning_rate', learning_rate)
        '''
        clip_min = - max_norm/learning_rate
        clip_max = max_norm/learning_rate
        '''
        #Select Optimizer
        if Optimizer is 'ADAM':
            if Optimizer_params is None:
                self.optimizer = tf.train.AdamOptimizer(learning_rate)
            else:
                self.optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate, beta1=Optimizer_params['beta1'], beta2=Optimizer_params['beta2'], epsilon=Optimizer_params['epsilon'])
        elif Optimizer is 'RMS':
            if Optimizer_params is None:
                self.optimizer = tf.train.RMSPropOptimizer(learning_rate)
            else:
                self.optimizer = tf.train.RMSPropOptimizer(learning_rate=learning_rate, decay=Optimizer_params['decay'], momentum=Optimizer_params['momentum'], epsilon=Optimizer_params['epsilon'])
        elif Optimizer is 'SGD':
                self.optimizer= tf.train.GradientDescentOptimizer(learning_rate)
        '''#Failed gpu memory saving experiment
        vars = tf.trainable_variables()
        total_length = len(vars)/2
        first_half = []
        second_half = []
        for index,grad in enumerate(vars):
            if index < total_length:
                first_half.append(grad)
            else:
                second_half.append(grad)
        #grads1 = self.optimizer.compute_gradients(self.loss, var_list=first_half)
        #grads2 = self.optimizer.compute_gradients(self.loss, var_list=second_half)
                self.train_step = self.optimizer.minimize(self.loss,global_step=self.global_step, var_list=first_half)
        self.train_step2 = self.optimizer.minimize(self.loss,global_step=self.global_step, var_list=second_half)
        '''
        gradients, tvars = zip(*self.optimizer.compute_gradients(self.loss))
        
        if Gradient_norm is not None:
            gradients, _ = tf.clip_by_global_norm(gradients, Gradient_norm)

        self.train_step = self.optimizer.apply_gradients(zip(gradients,tvars), global_step=self.global_step)

    def Construct_Model(self):
        self.model_dict['Model_Type'] = Factory(**self.kwargs).get_model()

        print('Model Graph Keys')
        print(tf.get_default_graph().get_all_collection_keys())

        self.model_dict['Output'] = tf.get_collection(self.Model_name + '_Output')[0]
        self.model_dict['Input_ph'] = tf.get_collection(self.Model_name + '_Input_ph')[0]
        self.model_dict['Output_ph'] = tf.get_collection(self.Model_name + '_Output_ph')[0]
        self.model_dict['Dropout_prob_ph'] = tf.get_collection(self.Model_name + '_Dropout_prob_ph')[0]
        self.model_dict['State'] = tf.get_collection(self.Model_name + '_State')[0]
        self.model_dict['Reshaped_input'] = tf.get_collection(self.Model_name + '_Input_reshape')[0]
        if self.model_dict['Model_Type'] is 'Segmentation' :
            self.model_dict['Weight_ph'] = tf.get_collection(self.Model_name + '_Weight_ph')[0]

    def Construct_Accuracy_op(self):
        with tf.name_scope('accuracy'):
            if self.model_dict['Model_Type'] is 'Classification' :
                correct_prediction = tf.equal(tf.argmax(self.model_dict['Output'], 1), tf.argmax(self.model_dict['Output_ph'], 1))
                false_images = tf.boolean_mask(self.model_dict['Reshaped_input'], tf.logical_not(correct_prediction))
                tf.summary.image(name='False images', tensor=false_images)
                self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
                tf.summary.scalar('accuracy', self.accuracy)
                self.accuracy_op = True

            elif self.model_dict['Model_Type'] is 'Segmentation' :
                probs = tf.reshape((tf.sigmoid(self.model_dict['Output'])), shape=[ self.kwargs['Batch_size'], -1])
                lab = tf.reshape(self.model_dict['Output_ph'], shape=[self.kwargs['Batch_size'], -1])
                probs = tf.ceil(probs - 0.5 + 1e-10)
                intersection = tf.reduce_sum(probs * lab, axis=1) 
                union =  tf.reduce_sum(probs, 1) + tf.reduce_sum(lab, 1) 
                tf.summary.image(name='Input images',tensor = self.model_dict['Reshaped_input'])
                tf.summary.image(name='Mask',tensor = tf.reshape(self.model_dict['Output_ph'], [-1, self.kwargs['Image_width'], self.kwargs['Image_height'], 1]))
                tf.summary.image(name='Weight',tensor = tf.reshape(self.model_dict['Weight_ph'], [-1, self.kwargs['Image_width'], self.kwargs['Image_height'], 1]))
                tf.summary.image(name='Output',tensor = (tf.sigmoid(self.model_dict['Output'])))
                self.accuracy = tf.reduce_mean(2 * intersection / (union))
                tf.summary.scalar('accuracy', self.accuracy)
                self.accuracy_op = True

            #tf.cond(self.accuracy > 0.92, lambda: tf.summary.image(name='False images', tensor=false_images), lambda: tf.summary.tensor_summary(name='correct_predictions', tensor=correct_prediction))

    def Construct_Writers(self, session=None):
        #Get default session

        self.saver = tf.train.Saver()
        if session is None:
            session = tf.get_default_session()
        #if self.kwargs['Summary']:
        self.log_writer = tf.summary.FileWriter(self.kwargs['Save_dir'] + '/logs/', session.graph)
            #self.test_writer = tf.summary.FileWriter(self.kwargs['Save_dir'] + '/test/')
        #else:
            #graph_writer = tf.summary.FileWriter(self.kwargs['Save_dir'] + '/train/')
            #graph_writer.add_graph(session.graph)
            #graph_writer.close();

    def Construct_IO_dict(self, batch):
        if self.model_dict['Model_Type'] is 'Classification':
            return {self.model_dict['Input_ph']: batch[0], self.model_dict['Output_ph']: batch[1]}

        elif self.model_dict['Model_Type'] is 'Segmentation':
            return {self.model_dict['Input_ph']: batch[0], self.model_dict['Output_ph']: batch[1], self.model_dict['Weight_ph']: batch[2]}

    def Construct_Predict_op(self):
        with tf.name_scope('Predict'):
            if self.model_dict['Model_Type'] is 'Classification':
                self.Predict_op = tf.argmax(self.model_dict['Output'], 1)
            elif self.model_dict['Model_Type'] is 'Segmentation':
                self.Predict_op = tf.sigmoid(self.model_dict['Output'])

    def Try_restore(self,session=None):
        #Get default session
        if session is None:
            session = tf.get_default_session()
        latest_ckpt = tf.train.latest_checkpoint(self.kwargs['Save_dir'] + '/mdl/')
        if latest_ckpt:
            print('Ckpt_found')
            print(latest_ckpt)
            self.saver.restore(session,latest_ckpt)
        else:
            print('Ckpt_not_found')

    def Predict(self, input_data, session=None):
        #Get default session
        if session is None:
            session = tf.get_default_session()
        #Construct Predict dict
        IO_predict_dict = {self.model_dict['Input_ph']: input_data}

        #Construct Predict feed_dict
        predict_feed_dict = {**IO_predict_dict, **self.test_dict}
        out = session.run([self.Predict_op], feed_dict=predict_feed_dict)
        return(out)




    def Train_Iter(self, iterations, save_iterations, data, log_iteration=10, restore=True, session=None):
        #Get default session
        if session is None:
            session = tf.get_default_session()
        #Try restore
        if restore:
            print('Restoring Default session')
            self.Try_restore(session)
            print('Default session restored')
        self.merged = tf.summary.merge_all()
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(coord=coord)
        #session.run(self.global_step.initializer)
        for step in range(iterations):
            step = session.run([self.global_step])[0]
            print('Getting batch')
            batch = data.next_batch(self.kwargs['Batch_size'])            #IO feed dict
            IO_feed_dict = self.Construct_IO_dict(batch)            #Construct train dict
            print('Constructing IO feed dict')
            train_feed_dict = {**IO_feed_dict, **self.train_dict}

            #Train Step
            print('getting loss')
            loss = session.run([self.loss], feed_dict=train_feed_dict)
            print('train step first half loss')
            session.run([self.train_step], feed_dict=train_feed_dict)
            print ('Step: ',step+1,'Loss: ',loss)


            #saver block
            if(step + 1) % save_iterations == 0:
                print('Saving Checkpoint')
                self.saver.save(session, self.kwargs['Save_dir'] + '/mdl/' + self.Model_name + '.ckpt', global_step=self.global_step)

            #logger block
            if(step + 1) % log_iteration == 0:
                test_feed_dict = {**IO_feed_dict, **self.test_dict}               #Construst Test dict
                if self.accuracy_op:
                    summary, train_accuracy, glo_step = session.run([self.merged, self.accuracy, self.global_step], \
                                feed_dict=test_feed_dict)
                else:
                    summary, glo_step = session.run([self.merged, self.global_step], \
                                feed_dict=test_feed_dict)
                self.log_writer.add_summary(summary, glo_step)


        coord.request_stop()
        coord.join(threads)



