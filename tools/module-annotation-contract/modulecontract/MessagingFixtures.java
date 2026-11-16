package modulecontract;

@com.guicedee.kafka.KafkaConnectionOptions("MODULE_CONNECTION")
@com.guicedee.kafka.KafkaTopicCreate("MODULE_CREATED_TOPIC")
@com.guicedee.ibmmq.IBMMQConnectionOptions("MODULE_CONNECTION")
@com.guicedee.mailclient.MailConnectionOptions("MODULE_CONNECTION")
public final class MessagingFixtures {
    @com.guicedee.kafka.KafkaTopicDefinition("MODULE_TOPIC")
    public static class KafkaConsumer implements com.guicedee.kafka.KafkaTopicConsumer<String,String> {
        public void consume(io.vertx.kafka.client.consumer.KafkaConsumerRecord<String,String> record) {}
    }
    @com.guicedee.ibmmq.IBMMQQueueDefinition(value="MODULE_QUEUE", connection="MODULE_QUEUE_CONNECTION")
    public static class IbmConsumer implements com.guicedee.ibmmq.IBMMQConsumer {
        public void consume(jakarta.jms.Message message) {}
    }
}
