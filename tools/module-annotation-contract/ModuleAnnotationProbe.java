import com.guicedee.client.Environment;
import java.lang.annotation.Annotation;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;

public final class ModuleAnnotationProbe {
    static int checks;
    static void expect(boolean success, String message) {
        checks++;
        if (!success) throw new AssertionError(message);
    }
    static Object call(Class<?> type, Object target, String name, Object... args) throws Exception {
        for (Method method : type.getDeclaredMethods()) {
            if (!method.getName().equals(name) || method.getParameterCount() != args.length) continue;
            boolean matches = true;
            for (int i=0; i<args.length; i++) {
                if (args[i] != null && !method.getParameterTypes()[i].isInstance(args[i]) && !method.getParameterTypes()[i].isPrimitive()) matches = false;
            }
            if (!matches) continue;
            method.setAccessible(true);
            try { return method.invoke(target, args); }
            catch (InvocationTargetException e) { throw new AssertionError(type.getName()+"."+name, e.getCause()); }
        }
        throw new NoSuchMethodException(type.getName()+"."+name);
    }
    static Object call(String type, String name, Object... args) throws Exception {
        Class<?> cls = Class.forName(type);
        var constructor = cls.getDeclaredConstructor(); constructor.setAccessible(true);
        return call(cls, constructor.newInstance(), name, args);
    }
    static Annotation annotation(Class<?> type, Map<String,Object> values) {
        return (Annotation) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, (p,m,a) -> {
            if (m.getName().equals("annotationType")) return type;
            return values.getOrDefault(m.getName(), m.getDefaultValue());
        });
    }
    @FunctionalInterface interface Wrapper { Object wrap(Annotation raw) throws Exception; }

    static void strings(String typeName, Wrapper wrapper) throws Exception {
        Class<?> type = Class.forName(typeName);
        Map<String,Object> values = new HashMap<>();
        for (Method member : type.getDeclaredMethods()) {
            String key = "MODULE_TEXT_"+type.getSimpleName()+"_"+member.getName();
            if (member.getReturnType() == String.class) values.put(member.getName(), key);
            if (member.getReturnType() == String[].class) values.put(member.getName(), new String[]{key, "literal-entry"});
            System.setProperty(key, "resolved-"+member.getName());
        }
        Object resolved = wrapper.wrap(annotation(type, values));
        for (Method member : type.getDeclaredMethods()) {
            if (!values.containsKey(member.getName())) continue;
            Object value = member.invoke(resolved);
            Object expected = "resolved-"+member.getName();
            if (value instanceof String[] array) expect(Arrays.equals(array, new String[]{expected.toString(), "literal-entry"}), typeName+"."+member.getName()+" array");
            else expect(expected.equals(value), typeName+"."+member.getName()+" bare name: "+value);
            System.clearProperty("MODULE_TEXT_"+type.getSimpleName()+"_"+member.getName());
            Object literal = member.invoke(resolved);
            if (literal instanceof String[] array) expect(Arrays.equals(array, (String[])values.get(member.getName())), typeName+"."+member.getName()+" literal array");
            else expect(values.get(member.getName()).equals(literal), typeName+"."+member.getName()+" literal");
        }
    }

    static void scoped(String owner, String prefix) throws Exception {
        String scoped = prefix+"_TEST_HOST", global = prefix+"_HOST";
        System.setProperty("MODULE_REFERENCE", "bare-value");
        expect(call(owner,"envForName","test","HOST","MODULE_REFERENCE").equals("bare-value"), prefix+" bare");
        System.setProperty(global,"global-value");
        Files.writeString(Path.of(".env"), scoped+"=scoped-file\n"); Environment.reloadDotEnv();
        expect(call(owner,"envForName","test","HOST","MODULE_REFERENCE").equals("scoped-file"), prefix+" scoped file before global JVM");
        Files.writeString(Path.of(".env.local"), scoped+"=scoped-local\n"); Environment.reloadDotEnv();
        expect(call(owner,"envForName","test","HOST","MODULE_REFERENCE").equals("scoped-local"), prefix+" local before shared");
        System.setProperty(scoped, "MODULE_REFERENCE");
        expect(call(owner,"envForName","test","HOST","MODULE_REFERENCE").equals("MODULE_REFERENCE"), prefix+" explicit value not reinterpreted");
        System.setProperty(scoped, "");
        expect(call(owner,"envForName","test","HOST","MODULE_REFERENCE").equals(""), prefix+" explicit empty");
        System.clearProperty(scoped); System.clearProperty(global);
        Files.writeString(Path.of(".env"), ""); Files.writeString(Path.of(".env.local"), ""); Environment.reloadDotEnv();
        expect(call(owner,"envForName","test","HOST","MODULE_OS_REFERENCE").equals("os-value"), prefix+" OS reference");
    }

    public static void main(String[] args) throws Exception {
        String kafka="com.guicedee.kafka.implementations.KafkaPreStartup", ibm="com.guicedee.ibmmq.implementations.IBMMQPreStartup";
        String rabbit="com.guicedee.rabbit.implementations.RabbitMQPreStartup", mail="com.guicedee.mailclient.implementations.MailClientPreStartup";
        String consul="com.guicedee.consul.ConsulPreStartup", discovery="com.guicedee.vertx.servicediscovery.implementations.ServiceResolverPreStartup";
        for (var entry : Map.of(kafka,"KAFKA",ibm,"IBMMQ",rabbit,"RABBITMQ",mail,"MAIL",consul,"CONSUL",discovery,"SERVICE_RESOLVER").entrySet()) scoped(entry.getKey(),entry.getValue());
        strings("com.guicedee.kafka.KafkaConnectionOptions", a->call(kafka,"wrapConnectionOptions","test",a));
        strings("com.guicedee.kafka.KafkaTopicDefinition", a->call(kafka,"wrapTopicDefinition",a));
        strings("com.guicedee.kafka.KafkaTopicCreate", a->call(kafka,"wrapTopicCreate","test",a));
        strings("com.guicedee.ibmmq.IBMMQConnectionOptions", a->call(ibm,"wrapConnectionOptions","test",a));
        strings("com.guicedee.ibmmq.IBMMQQueueDefinition", a->call(ibm,"wrapQueueDefinition",a));
        strings("com.guicedee.ibmmq.IBMMQQueueOptions", a->call(ibm,"wrapQueueOptions","test",a));
        strings("com.guicedee.rabbit.RabbitConnectionOptions", a->call(rabbit,"wrapConnectionOptions",a));
        strings("com.guicedee.rabbit.QueueDefinition", a->call(rabbit,"wrapQueueDefinition",a));
        strings("com.guicedee.mailclient.MailConnectionOptions", a->call(mail,"wrapConnectionOptions","test",a));
        strings("com.guicedee.consul.ConsulOptions", a->call(consul,"wrapOptions",a));
        strings("com.guicedee.vertx.servicediscovery.ServiceResolverOptions", a->call(discovery,"wrapOptions",a));
        strings("com.guicedee.guicedhazelcast.HazelcastServerOptions", a->call("com.guicedee.guicedhazelcast.services.HazelcastPreStartup","wrapServerOptions",a));
        strings("com.guicedee.guicedhazelcast.HazelcastClientOptions", a->call("com.guicedee.guicedhazelcast.services.HazelcastClientPreStartup","wrapClientOptions",a));
        String rest="com.guicedee.rest.client.implementations.RestClientRegistry";
        strings("com.guicedee.rest.client.annotations.Endpoint", a->call(rest,"wrapEndpoint",a,"test"));
        strings("com.guicedee.rest.client.annotations.EndpointSecurity", a->call(rest,"wrapSecurity",a,"test"));
        strings("com.guicedee.rest.client.annotations.EndpointOptions", a->call(rest,"wrapOptions",a,"test"));
        restOverrides();
        cors();
        services();
        platforms();
        cloudPrecedence();
        messagingRegistration();
        logger();
        System.out.println("MODULE_ANNOTATION_CONTRACT_OK checks="+checks);
    }

    static void restOverrides() throws Exception {
        var raw = annotation(Class.forName("com.guicedee.rest.client.annotations.EndpointSecurity"), Map.of("token","MODULE_REFERENCE",
                "value", com.guicedee.rest.client.annotations.EndpointSecurity.SecurityType.Bearer));
        String owner="com.guicedee.rest.client.implementations.RestClientRegistry";
        System.setProperty("REST_CLIENT_TOKEN_test","MODULE_REFERENCE");
        Object resolved=call(owner,"wrapSecurity",raw,"test");
        expect(raw.annotationType().getMethod("token").invoke(resolved).equals("MODULE_REFERENCE"),"REST override stays literal");
        expect(call(owner,"wrapSecurity",resolved,"test")==resolved,"REST security wrapping idempotent");
        var rawEndpoint = (com.guicedee.rest.client.annotations.Endpoint) annotation(com.guicedee.rest.client.annotations.Endpoint.class,
                Map.of("url","https://example.test", "security",raw));
        var client = new com.guicedee.rest.client.RestClient<>(null,rawEndpoint,"test","https://example.test",Object.class,Object.class,Object.class);
        var headers = new ArrayList<String>();
        var request = Proxy.newProxyInstance(ModuleAnnotationProbe.class.getClassLoader(), new Class<?>[]{io.vertx.ext.web.client.HttpRequest.class}, (p,m,a)->{
            if(m.getName().equals("bearerTokenAuthentication")) headers.add((String)a[0]);
            return p;
        });
        call(client.getClass(),client,"applyAuthentication",request);
        expect(headers.equals(List.of("MODULE_REFERENCE")),"REST request preserves canonical token override");
        System.clearProperty("REST_CLIENT_TOKEN_test");
        var endpoint=annotation(Class.forName("com.guicedee.rest.client.annotations.Endpoint"),Map.of("url","MODULE_REFERENCE"));
        System.setProperty("REST_CLIENT_URL_test","MODULE_REFERENCE");
        Object wrapped=call(owner,"wrapEndpoint",endpoint,"test");
        expect(call(owner,"resolveConfiguredUrl", endpoint.annotationType().getMethod("url").invoke(wrapped)).equals("MODULE_REFERENCE"),"REST URL not resolved twice");
        System.clearProperty("REST_CLIENT_URL_test");
    }

    static void cors() throws Exception {
        System.setProperty("MODULE_ORIGIN","https://example.test");
        System.setProperty("MODULE_METHOD","PUT");
        System.setProperty("MODULE_HEADER","X-Test");
        Class<?> type=Class.forName("com.guicedee.rest.services.Cors");
        var ann=annotation(type,Map.of("allowedOrigins",new String[]{"MODULE_ORIGIN","https://literal.test"},"allowedMethods",new String[]{"MODULE_METHOD","GET"},"allowedHeaders",new String[]{"MODULE_HEADER","Literal"}));
        String owner="com.guicedee.rest.implementations.CorsHandlerConfigurator";
        expect(call(owner,"getAllowedOrigins",ann).equals(Set.of("https://example.test","https://literal.test")),"CORS origin entries");
        expect(call(owner,"getAllowedMethods",ann).toString().contains("PUT"),"CORS methods");
        expect(call(owner,"getAllowedHeaders",ann).equals(Set.of("X-Test","Literal")),"CORS headers");
    }

    static void services() throws Exception {
        var type=Class.forName("com.guicedee.service.registry.RegisteredService");
        var values=new HashMap<String,Object>();
        for (var method:type.getDeclaredMethods()) {
            if(method.getReturnType()==String.class) {
                String key="MODULE_SERVICE_"+method.getName();
                System.setProperty(key,method.getName().equals("url")?"https://service.test":method.getName().equals("healthUrl")?"https://health.test/ready":"resolved-"+method.getName());
                values.put(method.getName(),key);
            } else if(method.getReturnType()==String[].class) {
                String key="MODULE_SERVICE_"+method.getName(); System.setProperty(key,"resolved-"+method.getName());
                values.put(method.getName(),new String[]{key});
            }
        }
        call("com.guicedee.service.registry.implementations.ServiceRegistryPreStartup","registerService",annotation(type,values),"/ready",true,8080,"");
        var registry=Class.forName("com.guicedee.service.registry.ServiceRegistry");
        var all=(Map<?,?>)call(registry,null,"all");
        Object service=all.get("resolved-name");
        expect(service!=null,"resolved registry name");
        expect(call(service.getClass(),service,"url").equals("https://service.test"),"resolved registry URL");
        expect(call(service.getClass(),service,"healthPath").equals("resolved-healthPath"),"resolved registry health path");
        var metadata=(Map<?,?>)call(service.getClass(),service,"metadata");
        for(String key:List.of("healthUrl","expectedContentType","revision","openApiPath","openApiEnvironments","graphqlPath","graphqlEnvironments","authScheme","authTokenUrl","authScopes"))
            expect(metadata.get(key).equals(key.equals("healthUrl")?"https://health.test/ready":"resolved-"+key),"service metadata "+key);
        expect(call(registry,null,"url","resolved-aliases").equals("https://service.test"),"resolved alias");
    }

    static void platforms() throws Exception {
        Class<?> defaults=Class.forName("com.guicedee.runtime.autoconfigure.implementations.PlatformAnnotationDefaults");
        Map<String,String> providers=Map.ofEntries(
                Map.entry("AwsAppRunner","AwsAppRunner"),Map.entry("AwsEcs","AwsEcs"),Map.entry("AwsElasticBeanstalk","AwsElasticBeanstalk"),
                Map.entry("AwsLambda","AwsLambda"),Map.entry("AzureAppService","AzureAppService"),Map.entry("AzureContainerApps","AzureContainerApps"),
                Map.entry("DigitalOceanApp","DigitalOceanAppPlatform"),Map.entry("FlyIo","FlyIo"),Map.entry("GcpAppEngine","GcpAppEngine"),
                Map.entry("GcpCloudRun","GcpCloudRun"),Map.entry("Heroku","Heroku"),Map.entry("Kubernetes","Kubernetes"),Map.entry("Railway","Railway"),Map.entry("Render","Render"));
        for(var entry:providers.entrySet()) {
            Class<?> type=Class.forName("com.guicedee.runtime.autoconfigure."+entry.getKey());
            Map<String,Object> values=new HashMap<>();
            for(var member:type.getDeclaredMethods()) if(member.getReturnType()==String.class) {
                String key="MODULE_PLATFORM_"+member.getName(); System.setProperty(key,"resolved-"+member.getName()); values.put(member.getName(),key);
            }
            call(defaults,null,"configure",annotation(type,values));
            Object environment=call("com.guicedee.runtime.autoconfigure.providers."+entry.getValue()+"EnvironmentProvider","runtimeEnvironment");
            String output=environment.toString();
            for(String attribute:values.keySet()) expect(output.contains("resolved-"+attribute),entry.getKey()+" consumed "+attribute+": "+output);
        }
        call(defaults,null,"configure",(Object)null);
    }

    static final class Logged {
        @com.guicedee.guicedinjection.InjectLogger("MODULE_LOGGER")
        org.apache.logging.log4j.Logger logger;
    }

    static void cloudPrecedence() throws Exception {
        Class<?> defaults=Class.forName("com.guicedee.runtime.autoconfigure.implementations.PlatformAnnotationDefaults");
        Class<?> lambda=Class.forName("com.guicedee.runtime.autoconfigure.AwsLambda");
        System.setProperty("MODULE_FUNCTION", "MODULE_NEXT_NAME");
        System.setProperty("MODULE_NEXT_NAME", "must-not-follow");
        System.setProperty("MODULE_REGION", "annotation-region");
        call(defaults,null,"configure",annotation(lambda,Map.of("functionName","MODULE_FUNCTION","region","MODULE_REGION")));
        String provider="com.guicedee.runtime.autoconfigure.providers.AwsLambdaEnvironmentProvider";
        Object detected=call(provider,"runtimeEnvironment");
        expect(call(detected.getClass(),detected,"serviceName").equals("MODULE_NEXT_NAME"),"platform bare reference is one hop");
        expect(call(provider,"detected").equals(false),"annotation does not fake cloud detection");
        System.setProperty("AWS_DEFAULT_REGION", "alias-region");
        detected=call(provider,"runtimeEnvironment");
        expect(call(detected.getClass(),detected,"region").equals("alias-region"),"provider alias before annotation");
        System.clearProperty("AWS_DEFAULT_REGION");
        Files.writeString(Path.of(".env"),"AWS_LAMBDA_FUNCTION_NAME=normal-file\n"); Environment.reloadDotEnv();
        expect(call(call(provider,"runtimeEnvironment").getClass(),call(provider,"runtimeEnvironment"),"serviceName").equals("normal-file"),"platform primary file before bare JVM");
        Files.writeString(Path.of(".env"),""); Environment.reloadDotEnv();
        call(defaults,null,"configure",(Object)null);

        Class<?> startup=Class.forName("com.guicedee.runtime.autoconfigure.implementations.RuntimeAutoConfigurePreStartup");
        Class<?> options=Class.forName("com.guicedee.runtime.autoconfigure.CloudRuntimeOptions");
        var field=startup.getDeclaredField("resolvedOptions");field.setAccessible(true);
        System.setProperty("MODULE_CONFIG_NAME","resolved-config");
        System.setProperty("MODULE_HEALTH_PATH","/resolved-health");
        field.set(null,annotation(options,Map.of("value","MODULE_CONFIG_NAME","healthPath","MODULE_HEALTH_PATH")));
        Object applied=call(startup,startup.getConstructor().newInstance(),"applyOverrides",detected);
        expect(call(applied.getClass(),applied,"serviceName").equals("MODULE_NEXT_NAME"),"detected value not treated as a second bare reference");
        var extras=(Map<?,?>)call(applied.getClass(),applied,"extras");
        expect(extras.get("configurationName").equals("resolved-config") && extras.get("healthPath").equals("/resolved-health"),"cloud name and health metadata");
        System.setProperty("CLOUD_RUNTIME_SERVICE_NAME","global");
        Files.writeString(Path.of(".env"),"CLOUD_RUNTIME_MODULE_CONFIG_NAME_SERVICE_NAME=scoped\n"); Environment.reloadDotEnv();
        applied=call(startup,startup.getConstructor().newInstance(),"applyOverrides",detected);
        expect(call(applied.getClass(),applied,"serviceName").equals("scoped"),"cloud scoped file before global JVM");
        System.clearProperty("CLOUD_RUNTIME_SERVICE_NAME");field.set(null,null);
        Files.writeString(Path.of(".env"),""); Environment.reloadDotEnv();
    }

    static void messagingRegistration() throws Exception {
        System.setProperty("MODULE_CONNECTION","resolved-connection");
        System.setProperty("MODULE_TOPIC","resolved-topic");
        System.setProperty("MODULE_CREATED_TOPIC","resolved-created-topic");
        System.setProperty("MODULE_QUEUE","resolved-queue");
        System.setProperty("MODULE_QUEUE_CONNECTION","resolved-queue-connection");
        try(var scan=new io.github.classgraph.ClassGraph().enableClasspath().enableClassInfo().enableAnnotationInfo().enableFieldInfo()
                .ignoreClassVisibility().acceptPackages("modulecontract").scan()) {
            var declaration=scan.getClassInfo("modulecontract.MessagingFixtures");
            String kafka="com.guicedee.kafka.implementations.KafkaPreStartup";
            call(kafka,"processConnection",scan,declaration,new HashSet<Class<?>>(),false);
            expect(((Map<?,?>)call(kafka,"getPackageConnectionNames")).get("modulecontract").equals("resolved-connection"),"Kafka resolved connection registry");
            expect(((Map<?,?>)call(kafka,"getTopicConsumerDefinitions")).containsKey("resolved-topic"),"Kafka resolved consumer registry");
            expect(((Map<?,?>)call(kafka,"getTopicCreateDefinitions")).containsKey("resolved-created-topic"),"Kafka resolved create registry");
            String ibm="com.guicedee.ibmmq.implementations.IBMMQPreStartup";
            call(ibm,"processConnection",scan,declaration,new HashSet<Class<?>>(),false);
            expect(((Map<?,?>)call(ibm,"getPackageConnectionNames")).get("modulecontract").equals("resolved-connection"),"IBM resolved connection registry");
            expect(((Map<?,?>)call(ibm,"getQueueConsumerDefinitions")).containsKey("resolved-queue"),"IBM resolved consumer registry");
            expect(((Map<?,?>)call(ibm,"getQueueConnectionNames")).get("resolved-queue").equals("resolved-queue-connection"),"IBM resolved queue connection");
            String mail="com.guicedee.mailclient.implementations.MailClientPreStartup";
            call(mail,"processConnections",scan);
            expect(((Map<?,?>)call(mail,"getConnectionsByName")).containsKey("resolved-connection"),"mail resolved connection registry");
        }
    }
    static void logger() throws Exception {
        System.setProperty("MODULE_LOGGER","resolved.logger");
        Class<?> type=Class.forName("com.guicedee.guicedinjection.logging.Log4JMembersInjector");
        var constructor=type.getDeclaredConstructor(Field.class); constructor.setAccessible(true);
        Object injector=constructor.newInstance(Logged.class.getDeclaredField("logger"));
        var logged=new Logged(); call(type,injector,"injectMembers",logged);
        expect(logged.logger.getName().equals("resolved.logger"),"injected logger name");
    }
}
