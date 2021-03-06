import tensorflow as tf
from utils.Architect import Architect
from abc import abstractmethod


class Base_Classifier(Architect):
    """Base classification network class, inherited by all classification neural networks """
    Type = 'Classification'

    def __init__(self, kwargs):
        super().__init__()
        self.input_placeholder = tf.placeholder(tf.float32, shape=[None, kwargs['Image_width'], kwargs['Image_height'],
                                                       kwargs['Image_cspace']], name='Input')
        self.output_placeholder = tf.placeholder(tf.float32, shape=[None, kwargs['Classes']], name='Output')
        self.build_params = kwargs
        self.dropout_placeholder = tf.placeholder(tf.float32, name='Dropout')
        self.state_placeholder = tf.placeholder(tf.string, name='State')
        self.output = None

        self.loss = []

        self.train_step = None

        self.accuracy = tf.Variable(0.0, trainable=False)

    @abstractmethod
    def build_net(self):
        pass

    def construct_control_dict(self, Type='TEST'):
        if Type.upper() in 'TRAIN':
            return {self.dropout_placeholder: self.build_params['Dropout'], self.state_placeholder: self.build_params['State']}

        elif Type.upper() in 'TEST':
            return {self.dropout_placeholder: 1, self.state_placeholder: self.build_params['State']}

    def set_output(self):
        self.output = self.build_net()

    def set_accuracy_op(self):
        acc_decay = 0.99
        correct_prediction = tf.equal(tf.argmax(self.output, 1), tf.argmax(self.output_placeholder, 1))
        false_images = tf.boolean_mask(self.input_placeholder, tf.logical_not(correct_prediction))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        tf.summary.image(name='False images', tensor=false_images)
        tf.summary.scalar('accuracy', self.accuracy.assign(acc_decay * self.accuracy + (1 - acc_decay) * accuracy))

    def set_train_ops(self, optimizer):
        loss = tf.add_n(self.loss, 'Loss_accu')
        self.train_step = optimizer.minimize(loss, global_step=self.global_step)

    def construct_IO_dict(self, batch):
        return {self.input_placeholder: batch[0], self.output_placeholder: batch[1]}

    def predict(self, **kwargs):
        if kwargs['session'] is None:
            session = tf.get_default_session()
        else:
            session = kwargs['session']

        predict_io_dict = {self.input_placeholder: kwargs['Input_Im']}
        predict_feed_dict = {**predict_io_dict, **self.test_dict}
        return session.run([self.output], feed_dict=predict_feed_dict)

    def construct_loss(self):
        if self.output is None:
            self.set_output()
            cbe_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(labels=self.output_placeholder,\
                                                                                 logits=self.output))
        self.loss.append(cbe_loss)
        tf.summary.scalar('loss', cbe_loss)

    def train(self, **kwargs):
        if kwargs['session'] is None:
            session = tf.get_default_session()
        else:
            session = kwargs['session']

        batch = kwargs['data'].next_batch(self.build_params['Batch_size'])
        IO_feed_dict = self.construct_IO_dict(batch)
        train_dict = self.construct_control_dict(Type='Train')
        train_feed_dict = {**IO_feed_dict, **train_dict}
        session.run([self.train_step], feed_dict=train_feed_dict)

    def test(self, **kwargs):
        if kwargs['session'] is None:
            session = tf.get_default_session()
        else:
            session = kwargs['session']

        batch = kwargs['data'].next_batch(self.build_params['Batch_size'])
        IO_feed_dict = self.construct_IO_dict(batch)
        test_dict = self.construct_control_dict(Type='Test')
        test_feed_dict = {**IO_feed_dict, **test_dict}

        if self.accuracy is not None:
            summary, _ = session.run([kwargs['merged'], self.accuracy], feed_dict=test_feed_dict)

        else:
            summary = session.run([kwargs['merged']], feed_dict=test_feed_dict)[0]

        return summary