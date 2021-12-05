from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.types as tp
from pyspark.ml import Pipeline
from pyspark.ml.feature import StopWordsRemover, Word2Vec, RegexTokenizer
from pyspark.ml.classification import LogisticRegression
from pyspark.sql import Row
from sklearn.linear_model import SGDClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
import sklearn
import numpy as np
import pickle

sc= SparkContext("local[2]","sent")
spark = SparkSession.builder.appName("Sentiment").getOrCreate()
ssc = StreamingContext(sc, 1)

lines = ssc.socketTextStream('localhost', 6100)
columns=["score","tweet"]

def preprocessing(df):
	df_temp=np.array(df.select('tweet').collect())
	count_vect = CountVectorizer()
	X_train_counts = count_vect.fit_transform(df_temp.ravel())
	
	tf_transformer = TfidfTransformer(use_idf=False).fit(X_train_counts)
	X_train_tf = tf_transformer.transform(X_train_counts)
	
	batchsize=10000
	y=np.reshape(np.array(df.select('score').collect()),(10000,1))
	model = SGDClassifier(alpha=.0001, loss='log', penalty='l2', n_jobs=-1, shuffle=True)

	df2=model.partial_fit(X_train_tf,np.reshape(np.array(df.select('score').collect()),(10000,1)),classes=[0,4])
	y_pred=df2.predict(X_train_tf)
	accuracy=sklearn.metrics.accuracy_score(y,y_pred)	
	print(accuracy)

def temp(rdd):
	df=spark.read.json(rdd)
	for row in df.rdd.toLocalIterator():
		conv_df = spark.createDataFrame(row,columns)
		#conv_df.show()
		preprocessing(conv_df)
			
lines.foreachRDD(lambda rdd : temp(rdd))

ssc.start()
ssc.awaitTermination()
